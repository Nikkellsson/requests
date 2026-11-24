# Практична робота № 3
Характеризаційні тести для Requests 2.32.5, клас PreparedRequest.
Базовий коміт b25c87d7cb8d6a18a37fa12442b5f883f9e41741.
У Windows відкрийте PowerShell у папці для нового клону та виконайте:

```powershell
git clone --single-branch --branch practical-3 https://github.com/Nikkellsson/requests.git requests-pz3
cd requests-pz3
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r practical-3/requirements.txt
.\.venv\Scripts\python.exe practical-3/run.py
Get-Content practical-3/results/summary.json
Invoke-Item practical-3/results/html/index.html
```

Якщо матеріали взято з ZIP, розпакуйте папку practical-3 у корінь клону Requests v2.32.5 поруч із src і tests. Перейдіть у корінь клону, потім виконайте команди від створення .venv. Run.py сам вибирає локальний src для імпорту. Тести виконуються без HTTP-запитів. Встановлення залежностей із PyPI та клонування потребують інтернету.

Кожен із чотирьох запусків записує окремий JSON у results. У summary.json наведено метрики саме класу. HTML показує файл models.py цілком. Еталонні вимірювання містяться в observed_summary.json. Для відтворення початкових спостережень у PowerShell з кореня клону виконайте:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe practical-3/probe.py
```
