# mediathek-mcp 📺

سرور MCP **غیررسمی و فقط‌خواندنی** برای **مدیاتک آلمان** از طریق API رایگان [MediathekViewWeb](https://mediathekviewweb.de) — جست‌وجوی برنامه‌های ARD ،ZDF ،3sat ،ARTE ،Phoenix ،tagesschau24 ،KiKA و شبکه‌های منطقه‌ای. بدون کلید، بدون لاگین.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP آلمان» (به سبک سپهر). وابسته به MediathekView یا ARD یا ZDF نیست.

## برای ایجنت‌های هوش مصنوعی

به تنظیمات MCP اضافه کنید (stdio):

```json
{
  "mcpServers": {
    "mediathek": {
      "command": "uvx",
      "args": ["mediathek-mcp==0.1.1"]
    }
  }
}
```

یا اجرای محلی: `python -m mediathek_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|------|
| `mediathek_search_programmes` | جست‌وجوی برنامه‌ها با عنوان، موضوع یا توضیح — `query` (مثل «Tagesschau»)، `channel` اختیاری (مثل «ZDF»)، `limit` از ۱ تا ۵۰ |
| `mediathek_latest_broadcasts` | جدیدترین برنامه‌های همهٔ شبکه‌ها، از جدید به قدیم — `limit` از ۱ تا ۵۰ |
| `mediathek_by_channel` | جدیدترین برنامه‌های یک شبکه — `channel` (مثل «ZDF»، «ARD»، «3sat»، «ARTE.DE»، «PHOENIX»)، `limit` از ۱ تا ۵۰ |
| `mediathek_by_topic` | همهٔ قسمت‌های یک برنامه/سریال — `topic` (مثل «heute journal»)، `limit` از ۱ تا ۵۰ |
| `mediathek_programme_detail` | جزئیات کامل یک برنامه: همهٔ لینک‌های ویدیو (کم‌کیفیت/معمولی/HD)، لینک زیرنویس و لینک وب‌سایت — `title` (دقیق)، `channel` اختیاری |
| `mediathek_list_channels` | شبکه‌های فهرست فیلم (فهرست انتخاب‌شده — API اندپوینت فهرست شبکه ندارد) |

نکته‌ها:
- فهرست فیلم حدود ۷۰۰٬۰۰۰ برنامه دارد و چند بار در روز به‌روز می‌شود؛ نتایج از جدید به قدیم مرتب‌اند.
- «جدیدترین برنامه‌ها» با جست‌وجوی پرتکرارترین حرف در عنوان/موضوع/توضیح کار می‌کند — API برای پرس‌وجوی خالی چیزی برنمی‌گرداند و کاراکتر جایگزین ندارد؛ نتیجه عملاً جدیدترین برنامه‌هاست.
- فیلتر شبکه در `mediathek_search_programmes` سمت کلاینت روی جدیدترین ۵۰ نتیجهٔ متنی اعمال می‌شود (API پرس‌وجوی AND ندارد)؛ `mediathek_by_channel` مستقیم شبکه را می‌پرسد.
- مقدار `total_results` برای پرس‌وجوهای خیلی گسترده از طرف API به ۱۰٬۰۰۰ محدود است.
- لینک‌های ویدیو مستقیم MP4 هستند (کم‌کیفیت / معمولی / HD)؛ اگر زیرنویس نباشد `subtitle_url` خالی است.
- داده: API عمومی MediathekViewWeb — بدون کلید، بدون لاگین، فقط‌خواندنی.

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — آفلاین، با پاسخ‌های واقعی ضبط‌شده از API (۱۹ تست)
- `tests/test_live.py` — چند درخواست زندهٔ محتاطانه به mediathekviewweb.de (۶ تست)

تست‌ها: ۲۵ از ۲۵ سبز (۱۹ آفلاین + ۶ زنده، ۲۰۲۶-۱۱-۰۹).

## مجوز

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
