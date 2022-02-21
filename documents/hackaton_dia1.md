# Hackaton: Dia 1
## 21.2.2022

### Problemas

- Parece que al hacer push no se me actualiza el github... => **SOLUCIONADO**

### 1º issue: Create list service and version tools

Crear un script similar a la herramienta nfcore/tools:
- **nf-core list**

Tendria que hacer algo asi de inicio...

```
$ nf-core list

                                          ,--./,-.
          ___     __   __   __   ___     /,-._.--~\
    |\ | |__  __ /  ` /  \ |__) |__         }  {
    | \| |       \__, \__/ |  \ |___     \`-._,-`-,
                                          `._,._,'

    nf-core/tools version 2.2

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Pipeline Name     ┃ Stars ┃ Latest Release ┃      Released ┃  Last Pulled ┃ Have latest release?  ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ rnafusion         │    45 │          1.2.0 │   2 weeks ago │            - │ -                     │
│ hic               │    17 │          1.2.1 │   3 weeks ago │ 4 months ago │ No (v1.1.0)           │
│ chipseq           │    56 │          1.2.0 │   4 weeks ago │  4 weeks ago │ No (dev - bfe7eb3)    │
│ atacseq           │    40 │          1.2.0 │   4 weeks ago │  6 hours ago │ No (master - 79bc7c2) │
│ viralrecon        │    20 │          1.1.0 │  1 months ago │ 1 months ago │ Yes (v1.1.0)          │
│ sarek             │    59 │          2.6.1 │  1 months ago │            - │ -                     │
```