"""Desktop app (builds to CorelAgent.exe): prompt box + live log."""
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

CONFIG = Path(os.environ.get("APPDATA", Path.home())) / "CorelAgent" / "key.txt"


def load_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY") or (CONFIG.read_text().strip() if CONFIG.exists() else "")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CorelDRAW Agent")
        self.geometry("720x520")
        self.q: queue.Queue[str] = queue.Queue()

        tk.Label(self, text="Anthropic API key").pack(anchor="w", padx=8, pady=(8, 0))
        self.key = tk.Entry(self, show="*")
        self.key.insert(0, load_key())
        self.key.pack(fill="x", padx=8)

        tk.Label(self, text="Nima chizish kerak?").pack(anchor="w", padx=8, pady=(8, 0))
        self.prompt = tk.Text(self, height=4)
        self.prompt.pack(fill="x", padx=8)

        bar = tk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        self.dry = tk.BooleanVar()
        tk.Checkbutton(bar, text="Dry-run (CorelDRAW'siz)", variable=self.dry).pack(side="left")
        self.btn = tk.Button(bar, text="Chizish", command=self.start)
        self.btn.pack(side="right")

        lz = tk.LabelFrame(self, text="Lazer (CO2): rasm -> kesish konturi (API kalit kerak emas)")
        lz.pack(fill="x", padx=8, pady=(0, 6))
        self.img = tk.Entry(lz)
        self.img.grid(row=0, column=0, columnspan=4, sticky="we", padx=4, pady=4)
        tk.Button(lz, text="Rasm tanlash...", command=self.pick).grid(row=0, column=4, padx=4)
        tk.Label(lz, text="Kengligi, mm").grid(row=1, column=0)
        self.wmm = tk.Entry(lz, width=6)
        self.wmm.insert(0, "200")
        self.wmm.grid(row=1, column=1)
        tk.Label(lz, text="Material, mm").grid(row=1, column=2)
        self.mat = tk.Entry(lz, width=6)
        self.mat.insert(0, "3")
        self.mat.grid(row=1, column=3)
        self.inv = tk.BooleanVar()
        tk.Checkbutton(lz, text="Invert", variable=self.inv).grid(row=1, column=4)
        self.lbtn = tk.Button(lz, text="Lazer uchun kesish", command=self.laser)
        self.lbtn.grid(row=2, column=0, columnspan=5, pady=4)
        lz.columnconfigure(0, weight=1)

        self.log = scrolledtext.ScrolledText(self, state="disabled")
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.after(100, self.pump)

    def pump(self) -> None:
        while not self.q.empty():
            self.log.configure(state="normal")
            self.log.insert("end", self.q.get() + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(100, self.pump)

    def pick(self) -> None:
        f = filedialog.askopenfilename(filetypes=[("Rasm", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if f:
            self.img.delete(0, "end")
            self.img.insert(0, f)

    def laser(self) -> None:
        try:
            path, w, m = self.img.get().strip(), float(self.wmm.get()), float(self.mat.get())
        except ValueError:
            messagebox.showwarning("Diqqat", "Kenglik va material raqam bo'lishi kerak")
            return
        if not path:
            messagebox.showwarning("Diqqat", "Avval rasm tanlang")
            return
        self.lbtn.configure(state="normal")
        threading.Thread(target=self.laser_work, args=(path, w, m, self.inv.get(), self.dry.get()), daemon=True).start()

    def laser_work(self, path: str, w: float, m: float, inv: bool, dry: bool) -> None:
        try:
            from coreldraw_agent.laser import run_image
            backend = None
            if not dry:
                from coreldraw_agent.backend import CorelBackend
                backend = CorelBackend()
            res = run_image(path, w, backend, material_mm=m, invert=inv)
            self.q.put(f"Kontur: {len(res.parts)} detal, {res.width_mm:.0f}x{res.height_mm:.0f} mm")
            self.q.put("SVG saqlandi: rasm yonida *.laser.svg")
            for msg in res.warnings:
                self.q.put("OGOHLANTIRISH: " + msg)
        except Exception as exc:
            self.q.put(f"XATO: {type(exc).__name__}: {exc}")

    def start(self) -> None:
        key, text = self.key.get().strip(), self.prompt.get("1.0", "end").strip()
        if not key or not text:
            messagebox.showwarning("Diqqat", "API key va promptni kiriting")
            return
        os.environ["ANTHROPIC_API_KEY"] = key
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(key)
        self.btn.configure(state="disabled")
        threading.Thread(target=self.work, args=(text, self.dry.get()), daemon=True).start()

    def work(self, text: str, dry: bool) -> None:
        import builtins
        import contextlib
        import io

        class Sink(io.TextIOBase):
            def write(s, data):  # noqa: N805
                if data.strip():
                    self.q.put(data.rstrip())
                return len(data)

        try:
            from coreldraw_agent.agent import run
            if dry:
                from coreldraw_agent.backend import MockBackend
                backend = MockBackend()
            else:
                from coreldraw_agent.backend import CorelBackend
                backend = CorelBackend()
            with contextlib.redirect_stdout(Sink()):
                result = run(text, backend)
            self.q.put(f"\nTayyor: {result}")
        except Exception as exc:
            self.q.put(f"XATO: {type(exc).__name__}: {exc}")
        finally:
            self.after(0, lambda: self.btn.configure(state="normal"))


if __name__ == "__main__":
    App().mainloop()
