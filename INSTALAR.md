# Instalação do RSAS 4.0

Este guia descreve todas as formas de instalar o **RSAS (RNA Structure Analysis Suite) 4.0** em Linux, macOS e Windows: ambiente Conda, imagem Docker e instalação nativa com Python em cada sistema operacional. Também cobre os programas opcionais RNArobo e Knotty, a verificação da instalação e a solução de problemas.

*English version: [INSTALL.md](INSTALL.md).*

> [!TIP]
> **Versão curta.** Instale o [Miniforge](https://github.com/conda-forge/miniforge) e rode
> `conda env create -f environment.yml` (Linux/macOS) ou `conda env create -f environment-windows.yml` (Windows),
> depois `conda activate rsas` e `python main.py`.

## Sumário

1. [O que é instalado](#1-o-que-é-instalado)
2. [Escolhendo o método de instalação](#2-escolhendo-o-método-de-instalação)
3. [Requisitos do sistema](#3-requisitos-do-sistema)
4. [Obtendo o código-fonte](#4-obtendo-o-código-fonte)
5. [Método A: Conda (recomendado)](#5-método-a-conda-recomendado)
6. [Método B: Docker](#6-método-b-docker)
7. [Método C: Instalação nativa](#7-método-c-instalação-nativa)
    - [Windows](#71-windows)
    - [macOS](#72-macos)
    - [Linux](#73-linux)
    - [Avisos de segurança do macOS (Gatekeeper)](#74-avisos-de-segurança-do-macos-gatekeeper)
8. [Programas opcionais: RNArobo e Knotty](#8-programas-opcionais-rnarobo-e-knotty)
9. [Verificando a instalação](#9-verificando-a-instalação)
10. [Executando o RSAS](#10-executando-o-rsas)
11. [Gerando um aplicativo independente](#11-gerando-um-aplicativo-independente)
12. [Atualização e desinstalação](#12-atualização-e-desinstalação)
13. [Solução de problemas](#13-solução-de-problemas)
14. [Situação da validação deste guia](#14-situação-da-validação-deste-guia)

---

## 1. O que é instalado

| Componente | Função | Origem |
|---|---|---|
| **Python 3.10 – 3.13** | Ambiente de execução (3.11 recomendado) | Conda, python.org ou o gerenciador de pacotes do sistema |
| **ViennaRNA ≥ 2.6** | Dobramento de RNA: MFE, função de partição, probabilidades de pareamento (módulo Python `RNA`) | Bioconda ou o pacote oficial (wheel) do PyPI |
| **customtkinter 5.x + Tk 8.6** | Interface gráfica | PyPI / Bioconda; o Tk vem com o Python |
| **numpy, openpyxl, biopython** | Análise e saída em Excel | PyPI / conda-forge |
| **python-pptx, matplotlib, pillow, lxml** | RNAfold Deck: desenhos das estruturas e PowerPoint | PyPI / conda-forge |
| **RNArobo 2.1.0** *(opcional)* | Página RNArobo Search (busca de motivos estruturais) | Incluído para macOS e Windows; executável para Linux distribuído pelos autores; código-fonte ([§8](#8-programas-opcionais-rnarobo-e-knotty)) |
| **Knotty** *(opcional)* | Página Pseudoknot Finder | Incluído para macOS e Windows; compilado a partir do código-fonte no Linux ([§8](#8-programas-opcionais-rnarobo-e-knotty)) |

O RSAS **não precisa de internet nem de navegador** para funcionar. Todo o dobramento, inclusive os desenhos de estrutura do RNAfold Deck, é feito localmente com o ViennaRNA. A única exceção é a aba opcional *Fetch from NCBI* do Sequence Extractor.

## 2. Escolhendo o método de instalação

| Método | Indicado para | Interface gráfica | Linha de comando | RNArobo / Knotty |
|---|---|:---:|:---:|---|
| **A. Conda** | A maioria dos usuários, em qualquer sistema. Um comando, reprodutível | ✅ | ✅ | macOS, Windows: incluídos. Linux: baixar/compilar |
| **B. Docker** | Servidores, clusters (HPC), pipelines, análises em lote reprodutíveis | ⚠️ precisa de servidor X | ✅ | Montar os executáveis Linux no contêiner |
| **C. Nativa (venv + pip)** | Quem não usa Conda ou prefere gerenciar o próprio Python | ✅ | ✅ | Igual ao Conda |

> [!NOTE]
> Os três métodos instalam o mesmo código e a mesma versão do ViennaRNA (2.7.2 quando este guia foi escrito). Os resultados são idênticos em todos os métodos e sistemas operacionais.

## 3. Requisitos do sistema

| | Mínimo | Recomendado |
|---|---|---|
| **Sistema operacional** | Windows 10 (64 bits), macOS 11 Big Sur, ou Linux com glibc ≥ 2.24 (Ubuntu 18.04+, Debian 10+, RHEL/Rocky 8+) | Windows 11, macOS 13+, Ubuntu 22.04/24.04 |
| **Arquitetura** | x86_64, ou ARM64 no macOS (Apple Silicon) e no Linux | Qualquer uma delas |
| **Python** | 3.10 | 3.11 ou 3.12 |
| **Memória** | 4 GB | 8 GB ou mais para lotes grandes e função de partição |
| **Disco** | 1,5 GB (ambiente Conda) | 3 GB |
| **Tela** | Necessária apenas para a interface gráfica | — |

> [!WARNING]
> O Windows em ARM não é suportado nativamente, porque não existe ViennaRNA para essa plataforma. Use o WSL2 ou o Docker.

## 4. Obtendo o código-fonte

**Com Git** (recomendado; facilita as atualizações):

```bash
git clone https://github.com/<dono>/RSAS.git
cd RSAS
git checkout v4.0.0
```

Substitua `<dono>` pela conta do GitHub que hospeda a sua cópia do RSAS.

**Sem Git:** na página do repositório, clique em **Code → Download ZIP**, extraia o arquivo e abra um terminal na pasta extraída.

Todos os comandos abaixo são executados **na raiz do repositório**, a pasta que contém o `main.py`.

---

## 5. Método A: Conda (recomendado)

O Conda instala o Python, o Tk e o ViennaRNA já compilados, sem precisar de compilador nem de pacotes do sistema. O repositório traz dois arquivos de ambiente:

| Arquivo | Plataformas | Origem do ViennaRNA |
|---|---|---|
| `environment.yml` | Linux (x86_64), macOS Intel, macOS Apple Silicon | Bioconda (compilação nativa) |
| `environment-windows.yml` | Windows 10/11 (x86_64) | Wheel oficial do PyPI (o Bioconda não tem versão para Windows) |

### 5.1 Instalar uma distribuição Conda

Instale o **[Miniforge](https://github.com/conda-forge/miniforge)**. É um instalador mínimo que usa por padrão o canal comunitário `conda-forge` e inclui o `mamba`, um substituto mais rápido do `conda`. Miniconda e Anaconda também funcionam.

<details>
<summary><b>Linux / macOS</b></summary>

```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh -b -p "$HOME/miniforge3"
"$HOME/miniforge3/bin/conda" init "$(basename "$SHELL")"
# Feche e abra o terminal novamente.
```

</details>

<details>
<summary><b>Windows</b></summary>

1. Baixe o `Miniforge3-Windows-x86_64.exe` na [página de versões do Miniforge](https://github.com/conda-forge/miniforge/releases/latest).
2. Execute o instalador e mantenha a opção padrão *Just Me*.
3. Abra o **Miniforge Prompt** pelo menu Iniciar. Use esse prompt para todos os comandos abaixo.

</details>

### 5.2 Criar o ambiente

**Linux e macOS:**

```bash
conda env create -f environment.yml
conda activate rsas
```

**Windows (Miniforge Prompt):**

```bat
conda env create -f environment-windows.yml
conda activate rsas
```

> [!TIP]
> Troque `conda` por `mamba` no comando `env create` para uma resolução de dependências mais rápida.

O ambiente se chama `rsas`. Ative-o em cada terminal novo antes de usar o RSAS.

### 5.3 Instalar os comandos do RSAS (opcional)

```bash
python -m pip install --no-deps -e .
```

Isso cria dois comandos no ambiente: `rsas` (aplicativo gráfico) e `rsas-cli` (linha de comando). Sem esse passo, use `python main.py` e `python -m RnaThermofinder`, que são equivalentes.

### 5.4 Verificar e executar

```bash
python -m RnaThermofinder version     # RSAS 4.0.0 | ViennaRNA 2.7.2 | Python 3.11.x
python -m pytest -q tests             # todos os testes devem passar
python main.py                        # abre o aplicativo
```

Se for usar o RNArobo Search ou o Pseudoknot Finder, siga para a [§8](#8-programas-opcionais-rnarobo-e-knotty).

---

## 6. Método B: Docker

A imagem Docker contém o ambiente Linux completo: ViennaRNA, a linha de comando do RSAS e o RNAfold Deck. Ela é construída a partir do mesmo `environment.yml` do Método A, e a construção roda a bateria de testes; se a construção terminar, a instalação está verificada.

### 6.1 Pré-requisitos

- **Linux:** Docker Engine 20.10 ou mais recente ([instruções de instalação](https://docs.docker.com/engine/install/)). Adicione seu usuário ao grupo `docker`, ou use `sudo` antes dos comandos abaixo.
- **macOS / Windows:** [Docker Desktop](https://www.docker.com/products/docker-desktop/). No Windows, ative o back-end WSL2, que já é o padrão.

### 6.2 Construir a imagem

Na raiz do repositório:

```bash
docker build -t rsas:4.0.0 .
```

A construção leva alguns minutos: baixa os pacotes Conda e roda os testes. Todas as dependências existem para `linux/amd64` e `linux/arm64`, então o Docker gera uma imagem nativa tanto em máquinas Intel/AMD quanto em Apple Silicon.

### 6.3 Executar análises (sem tela)

O ponto de entrada do contêiner é a linha de comando do RSAS (`python -m RnaThermofinder`). Monte a pasta com os seus arquivos de entrada em `/data` e grave os resultados nela:

**Linux / macOS:**

```bash
docker run --rm -v "$PWD":/data rsas:4.0.0 version
docker run --rm -v "$PWD":/data rsas:4.0.0 analyze /data/minhas_sequencias.fasta --out-dir /data --cores 4
```

**Windows (PowerShell):**

```powershell
docker run --rm -v "${PWD}:/data" rsas:4.0.0 analyze /data/minhas_sequencias.fasta --out-dir /data --cores 4
```

Cada análise cria uma pasta nova, `minhas_sequencias_<AAAAmmdd_HHMMSS>/`, ao lado do arquivo de entrada. Todos os arquivos dentro dela começam com o nome da entrada. Para gerar um RNAfold Deck dessa análise (substitua `<run>` pelo nome da pasta):

```bash
docker run --rm -v "$PWD":/data rsas:4.0.0 deck \
  --results "/data/<run>/minhas_sequencias_rna_results.xlsx" \
  --tier "Tier 1" --fold both --temp 25 --temp 37 --temp 42 \
  --out-dir "/data/<run>" --name minhas_sequencias_RNAfold_deck
```

> [!NOTE]
> Os arquivos gravados pelo contêiner pertencem ao usuário do contêiner (UID 57439). No Linux, acrescente `--user "$(id -u):$(id -g)" -e HOME=/tmp` ao `docker run` para que os resultados fiquem no seu nome.

As configurações salvas pela interface (colunas de saída, perfis de pontuação, temperaturas) ficam em `~/.rsas/` dentro do contêiner. Para usar as suas, monte a pasta: `-v "$HOME/.rsas":/home/mambauser/.rsas`.

### 6.4 Abrir a interface gráfica pelo contêiner (opcional)

A interface precisa de uma tela X11. Para uso diário da interface, os Métodos A e C são mais simples; o Docker é voltado principalmente para uso sem tela.

<details>
<summary><b>Linux (X11 ou XWayland)</b></summary>

```bash
xhost +local:docker
docker run --rm -it -e DISPLAY="$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD":/data rsas:4.0.0 gui
xhost -local:docker
```

</details>

<details>
<summary><b>macOS (XQuartz)</b></summary>

1. Instale o [XQuartz](https://www.xquartz.org/), encerre a sessão e entre de novo.
2. Em **XQuartz → Settings → Security**, ative *Allow connections from network clients* e reinicie o XQuartz.
3. Execute:

```bash
xhost + 127.0.0.1
docker run --rm -it -e DISPLAY=host.docker.internal:0 -v "$PWD":/data rsas:4.0.0 gui
```

</details>

<details>
<summary><b>Windows 11 (WSLg)</b></summary>

Num terminal Ubuntu (WSL2), com a integração WSL do Docker Desktop ativada:

```bash
docker run --rm -it -e DISPLAY="$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /mnt/wslg:/mnt/wslg -v "$PWD":/data rsas:4.0.0 gui
```

</details>

---

## 7. Método C: Instalação nativa

A instalação nativa usa um ambiente virtual padrão do Python (`venv`) e o `pip`. O ViennaRNA é instalado pelo wheel oficial do PyPI, disponível para Python 3.10–3.13 no Windows x64, macOS (Intel e Apple Silicon) e Linux (x86_64 e aarch64). Não é preciso compilador.

### 7.1 Windows

**Passo 1. Instale o Python.** Baixe o **Python 3.11 ou 3.12 (64 bits)** em [python.org](https://www.python.org/downloads/windows/). No instalador:
- marque **Add python.exe to PATH**;
- mantenha **tcl/tk and IDLE** selecionado (necessário para a interface).

**Passo 2. Abra o PowerShell na pasta do RSAS** (no Explorador de Arquivos, *Shift + clique direito → Abrir no Terminal*) e crie o ambiente:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> [!NOTE]
> Se o PowerShell recusar o `Activate.ps1`, libere scripts locais uma vez com
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ou use o Prompt de Comando e rode `.venv\Scripts\activate.bat`.

**Passo 3. Verifique e execute:**

```powershell
python -m RnaThermofinder version
python main.py
```

**RNArobo e Knotty no Windows.** As versões Windows dos dois programas já vêm em `bin\windows\` (`rnarobo.exe`, `knotty.exe` e os parâmetros `simfold\` do Knotty), então todas as páginas funcionam nativamente; veja a [§8.3](#83-windows).

### 7.2 macOS

**Passo 1. Instale o Python 3.11 ou 3.12** pelo [python.org](https://www.python.org/downloads/macos/). O instalador *universal2* roda nativamente em Intel e Apple Silicon e traz um Tk que funciona. Depois de instalar, dê dois cliques em **Install Certificates.command**, em `/Applications/Python 3.x/`.

> [!WARNING]
> Evite o `/usr/bin/python3` da Apple (Command Line Tools). O Tk dele é antigo e a interface aparece com defeitos. Se preferir o Python do Homebrew, instale também o Tk correspondente, por exemplo `brew install python@3.12 python-tk@3.12`.

**Passo 2. Crie o ambiente** (Terminal, na pasta do RSAS):

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Passo 3. Verifique e execute:**

```bash
python -m RnaThermofinder version
python main.py
```

O RNArobo e o Knotty já vêm incluídos para macOS; veja a [§8.1](#81-macos-incluídos) para a configuração inicial. Se o macOS disser que o RSAS ou um desses programas *está danificado* ou *não pode ser verificado*, veja a [§7.4](#74-avisos-de-segurança-do-macos-gatekeeper).

### 7.3 Linux

**Passo 1. Instale o Python com suporte a Tk e venv.**

| Distribuição | Comando |
|---|---|
| Ubuntu / Debian | `sudo apt update && sudo apt install -y python3 python3-venv python3-pip python3-tk` |
| Fedora / RHEL / Rocky / Alma | `sudo dnf install -y python3 python3-pip python3-tkinter` |
| openSUSE | `sudo zypper install -y python3 python3-pip python3-tk` |
| Arch / Manjaro | `sudo pacman -S --needed python python-pip tk` |

Confira se o Python do sistema é 3.10 ou mais recente (`python3 --version`). Em distribuições antigas (por exemplo RHEL 8 ou Ubuntu 20.04), instale um Python mais novo, como o `python3.11` dos repositórios extras da distribuição, ou use o [Método A](#5-método-a-conda-recomendado).

**Passo 2. Crie o ambiente** (na pasta do RSAS):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Passo 3. Verifique e execute:**

```bash
python -m RnaThermofinder version
python main.py
```

Em servidores sem tela, use apenas a [linha de comando](#10-executando-o-rsas). Para abrir a interface num servidor, use redirecionamento X pelo SSH (`ssh -X`) ou uma tela virtual (`xvfb-run python main.py`).

### 7.4 Avisos de segurança do macOS (Gatekeeper)

O RSAS é um software acadêmico e não é notarizado pela Apple. Ao abrir o **RSAS.app** empacotado (da versão em `.dmg`), ou quando o RSAS executa os programas **`rnarobo`** e **`knotty`** de `bin/macos/`, o macOS pode recusar com uma destas mensagens:

- *"RSAS" is damaged and can't be opened. You should move it to the Trash.* ("O RSAS está danificado e não pode ser aberto.")
- *"RSAS" can't be opened because Apple cannot check it for malicious software.*
- *"rnarobo" cannot be opened because the developer cannot be verified.*

**Os arquivos não estão danificados.** O macOS marca todo arquivo baixado da internet com o atributo `com.apple.quarantine`. Quando um programa em quarentena é aberto, o **Gatekeeper** verifica se ele é assinado e notarizado pela Apple; se não for, o macOS bloqueia e mostra a mensagem (enganosa) de "danificado". Use as soluções abaixo, na ordem, e somente para cópias do RSAS baixadas do repositório oficial.

**Solução 1. Liberar nos Ajustes do Sistema (recomendada, a mais segura).**

1. Abra o RSAS uma vez; quando o erro aparecer, clique em **Cancelar** (ou **OK**).
2. Abra **Ajustes do Sistema → Privacidade e Segurança**.
3. Role até **Segurança**. Haverá uma mensagem dizendo que "RSAS" (ou "rnarobo" / "knotty") foi bloqueado por não ser de um desenvolvedor identificado.
4. Clique em **Abrir Mesmo Assim** (*Open Anyway*) e digite a senha do Mac. O RSAS abre, e o macOS guarda a escolha.

No macOS 15 (Sequoia) ou mais recente, o clique direito → **Abrir** não contorna mais essa verificação; use **Abrir Mesmo Assim**, como acima.

**Solução 2. Remover a quarentena no Terminal** (se **Abrir Mesmo Assim** não aparecer):

```bash
# O aplicativo instalado em /Applications
sudo xattr -cr /Applications/RSAS.app

# Os executáveis do RNArobo e do Knotty na pasta do RSAS (sem sudo: a pasta é sua)
cd /caminho/para/RSAS
xattr -dr com.apple.quarantine bin/macos
chmod +x bin/macos/rnarobo bin/macos/knotty
```

Dica: digite `sudo xattr -cr ` (com um espaço no final) e arraste o **RSAS.app** do Finder para a janela do Terminal para preencher o caminho. Depois, abra o RSAS de novo. Se a mensagem de "danificado" continuar, vá em **Ajustes do Sistema → Privacidade e Segurança**, onde **Abrir Mesmo Assim** deve estar disponível agora (Solução 1, passos 3–4).

O DMG também traz o **Install RSAS.sh**, que copia o RSAS.app para `/Applications` e remove a quarentena de uma vez.

*Se o Terminal responder "Operation not permitted"*, ele não tem permissão para alterar o arquivo:

1. Abra **Ajustes do Sistema → Privacidade e Segurança → Acesso Total ao Disco**.
2. Desbloqueie se necessário, clique em **+**, escolha **Aplicativos → Utilitários → Terminal.app** e ative a chave.
3. Feche o Terminal completamente, abra-o de novo e repita o comando `xattr`.

**Solução 3. Desativar o Gatekeeper temporariamente** (se os comandos acima falharem). Reative logo depois que o RSAS abrir uma vez:

```bash
sudo spctl --master-disable     # versões recentes também pedem confirmação em Privacidade e Segurança ("Qualquer lugar")
open /Applications/RSAS.app
sudo spctl --master-enable      # reative o Gatekeeper imediatamente
```

**Solução 4. Assinatura ad hoc** (último recurso). Assine o programa localmente com uma assinatura ad hoc:

```bash
sudo codesign --force --deep --sign - /Applications/RSAS.app
codesign --force --sign - bin/macos/rnarobo bin/macos/knotty      # a partir da pasta do RSAS
```

| Passo | Método | Quando usar |
|---|---|---|
| 1 | Ajustes do Sistema → Privacidade e Segurança → **Abrir Mesmo Assim** | Primeira opção; a mais segura |
| 2 | `xattr` (remover quarentena), depois **Abrir Mesmo Assim** | Quando **Abrir Mesmo Assim** não aparece; também é o passo único padrão para `bin/macos/` |
| 3 | Desativar o Gatekeeper temporariamente | Quando os comandos do Terminal falham; reative em seguida |
| 4 | Assinatura ad hoc | Último recurso |

Rodar o RSAS pelo código-fonte (Conda ou `python main.py`) não dispara esses avisos para o próprio RSAS, porque o Python já é confiável; só os executáveis `rnarobo` e `knotty` de `bin/macos/` precisam da Solução 2, uma vez.

---

## 8. Programas opcionais: RNArobo e Knotty

Só duas páginas dependem de programas externos: **RNArobo Search** (`rnarobo`) e **Pseudoknot Finder** (`knotty`). Todo o resto, inclusive a análise principal e o RNAfold Deck, funciona sem eles.

> [!NOTE]
> **Não é preciso ser administrador.** Nesta seção, `bin/` sempre significa a pasta `bin/` **dentro da pasta do RSAS** (por exemplo `~/RSAS/bin/linux/`), e não uma pasta do sistema como `/usr/bin`. Todos os comandos desta seção gravam apenas na pasta do RSAS ou numa pasta temporária.

O RSAS procura cada executável nesta ordem:

1. dentro do aplicativo empacotado (versão PyInstaller);
2. em `bin/<plataforma>/` da pasta do RSAS: `bin/macos/`, `bin/linux/` ou `bin/windows/`;
3. no `PATH` (uma pasta do próprio usuário no `PATH`, como `~/.local/bin`, também funciona).

O Knotty também precisa da pasta de parâmetros de energia, `simfold/`, ao lado do executável `knotty`. Quando o programa é encontrado, a página mostra uma faixa verde com o caminho dele.

| Programa | Autores e origem | Licença | Referência |
|---|---|---|---|
| **RNArobo 2.1.0** | Computational Biology, Comenius University in Bratislava: <https://compbio.fmph.uniba.sk/software.php> (versão mais recente: <https://github.com/rampasek/RNArobo>) | GPL-3.0 | Rampášek L, Jimenez RM, Lupták A, Vinař T, Brejová B. *RNA motif search with data-driven element ordering.* BMC Bioinformatics 17:216 (2016) |
| **Knotty** | Hosna Jabbari, University of Alberta: <https://github.com/HosnaJabbari/Knotty> (parâmetros de energia do SimFold/MultiRNAFold) | GPL | Jabbari H, Wark I, Montemagno C, Will S. *Knotty: efficient and accurate prediction of complex RNA pseudoknot structures.* Bioinformatics 34:3849–3856 (2018) |

Nos comandos abaixo, troque `/caminho/para/RSAS` pela pasta do RSAS (a que contém o `main.py`).

### 8.1 macOS (incluídos)

Os dois executáveis vêm em `bin/macos/`, junto com os parâmetros do Knotty. São versões Intel (x86_64):

```bash
cd /caminho/para/RSAS

# Somente Apple Silicon: instale o Rosetta 2 uma vez
softwareupdate --install-rosetta --agree-to-license

# Remova a marca de quarentena do download para o macOS permitir os executáveis
xattr -dr com.apple.quarantine bin/macos
chmod +x bin/macos/rnarobo bin/macos/knotty
```

Se o macOS ainda bloquear o `rnarobo` ou o `knotty` (*cannot be opened because the developer cannot be verified*), libere-os em **Ajustes do Sistema → Privacidade e Segurança → Abrir Mesmo Assim**, ou siga as outras soluções da [§7.4](#74-avisos-de-segurança-do-macos-gatekeeper).

Para usar versões nativas de Apple Silicon, compile os dois programas a partir do código-fonte ([§8.4](#84-compilando-a-partir-do-código-fonte-macos-e-linux)) e copie-os para `bin/macos/`, substituindo os incluídos.

### 8.2 Linux e WSL2

**RNArobo: baixe o executável pronto para Linux** (64 bits) publicado pelos autores, direto para a pasta do RSAS:

```bash
cd /caminho/para/RSAS
mkdir -p bin/linux
curl -L -o bin/linux/rnarobo https://compbio.fmph.uniba.sk/rnarobo/rnarobo-2.1.0-linux64
#   (ou: wget -O bin/linux/rnarobo https://compbio.fmph.uniba.sk/rnarobo/rnarobo-2.1.0-linux64)
chmod +x bin/linux/rnarobo
bin/linux/rnarobo 2>&1 | head -n 5          # mostra as instruções de uso
```

Se esse executável não rodar na sua distribuição, compile o RNArobo a partir do código-fonte ([§8.4.1](#841-rnarobo-a-partir-do-código-fonte)).

**Knotty: compile a partir do código-fonte** e instale em `bin/linux/` ([§8.4.2](#842-knotty-a-partir-do-código-fonte)). Não existe executável pronto para Linux.

**Docker.** Para usar os programas dentro do contêiner, monte a pasta que contém `rnarobo`, `knotty` e `simfold/`:

```bash
docker run --rm -it -v "$PWD/bin/linux":/opt/rsas/bin/linux ... rsas:4.0.0 gui
```

### 8.3 Windows

Os dois programas vêm prontos para Windows em `bin\windows\`: `rnarobo.exe`, `knotty.exe` e os parâmetros de energia do Knotty em `bin\windows\simfold\`. O RSAS os encontra automaticamente; não é preciso instalar nada. Mantenha a pasta `simfold\` ao lado do `knotty.exe`.

Se o SmartScreen do Windows ou um antivírus bloquear o `rnarobo.exe` ou o `knotty.exe`, escolha **Mais informações → Executar assim mesmo**, ou libere o arquivo na Segurança do Windows. Como alternativa, rode o RSAS dentro do **WSL2** (Ubuntu) e siga a [§8.2](#82-linux-e-wsl2).

### 8.4 Compilando a partir do código-fonte (macOS e Linux)

É preciso um compilador C/C++ e o `make`:

| Sistema | Comando (uma vez) |
|---|---|
| macOS | `xcode-select --install` (Command Line Tools da Apple) |
| Debian / Ubuntu / WSL2 | `sudo apt install -y build-essential` |
| Fedora / RHEL / Rocky | `sudo dnf install -y gcc gcc-c++ make` |

Num servidor compartilhado sem acesso de administrador, os compiladores normalmente já estão instalados (`gcc --version`) ou disponíveis como módulo (`module load gcc`).

Defina duas variáveis para os comandos abaixo (`PLAT` é `macos` ou `linux`):

```bash
RSAS=/caminho/para/RSAS
PLAT=linux                       # ou: PLAT=macos
mkdir -p "$RSAS/bin/$PLAT"
```

#### 8.4.1 RNArobo a partir do código-fonte

Pelo arquivo da versão (RNArobo 2.1.0):

```bash
cd /tmp
curl -LO https://compbio.fmph.uniba.sk/rnarobo/rnarobo-2.1.0.tar.gz
tar -zxf rnarobo-2.1.0.tar.gz
cd rnarobo-2.1.0
make
cp rnarobo "$RSAS/bin/$PLAT/"
chmod +x "$RSAS/bin/$PLAT/rnarobo"
```

ou pela versão mais recente no GitHub:

```bash
cd /tmp
git clone https://github.com/rampasek/RNArobo.git
cd RNArobo
make
cp rnarobo "$RSAS/bin/$PLAT/"
```

O manual do RNArobo (formato dos descritores) está em <https://compbio.fmph.uniba.sk/rnarobo/rnarobo-readme.pdf>.

#### 8.4.2 Knotty a partir do código-fonte

O Knotty precisa de um compilador com suporte a C++11 (g++ 4.7.2 ou mais recente, ou o clang da Apple) e do **CMake 3.1 ou mais recente**. Confira com `cmake --version`. Se o CMake não estiver instalado ou for antigo, instale com uma destas opções:

```bash
conda install -n rsas -c conda-forge cmake      # no ambiente Conda do RSAS (sem administrador)
python -m pip install --user cmake              # qualquer Python, instalação do usuário (sem administrador)
brew install cmake                              # macOS com Homebrew (https://brew.sh)
sudo apt install -y cmake                       # Debian / Ubuntu / WSL2
```

Baixe, compile e instale o Knotty. Compile numa pasta que você vai manter (aqui, `~/tools/Knotty-master`), porque os autores do Knotty avisam que a pasta `simfold/` não deve ser apagada nem movida depois da compilação:

```bash
mkdir -p ~/tools && cd ~/tools
curl -L -o Knotty-master.zip https://github.com/HosnaJabbari/Knotty/archive/master.zip
unzip -q Knotty-master.zip
cd Knotty-master                 # a pasta que contém o README.md do Knotty

cmake -H. -Bbuild
cmake --build build
#   Erros de C++11? Apague a pasta build e indique o compilador:
#   rm -rf build && cmake -H. -Bbuild -DCMAKE_CXX_COMPILER=g++ && cmake --build build

# Instale na pasta do RSAS: o executável e os parâmetros de energia, lado a lado
cp "$(find . -maxdepth 2 -type f -name knotty -perm -u+x | head -n 1)" "$RSAS/bin/$PLAT/"
cp -R simfold "$RSAS/bin/$PLAT/"
chmod +x "$RSAS/bin/$PLAT/knotty"
```

O `git clone https://github.com/HosnaJabbari/Knotty.git` pode substituir as linhas de download e `unzip`. Se recompilar depois de mover a pasta do Knotty, apague antes a pasta `build/` dele.

### 8.5 Verificando os programas

```bash
cd /caminho/para/RSAS
python -c "from RnaThermofinder.utils.rnarobo_wrapper import check_rnarobo_available as c; print(c())"
python -c "from RnaThermofinder.utils.knotty_wrapper import check_knotty_available as c; print(c())"
(cd bin/linux && ./knotty GCAACGAUGACAUACAUCGCUAGUCGACGC -w)     # bin/macos no Mac
```

Cada linha `check_…` mostra `(True, '<caminho do executável>')`, e o teste do Knotty mostra uma estrutura em notação de parênteses com a energia. No aplicativo, as páginas RNArobo Search e Pseudoknot Finder mostram uma faixa verde.

---

## 9. Verificando a instalação

Rode estas verificações com o ambiente ativado, na raiz do repositório:

```bash
# 1. Versões
python -m RnaThermofinder version

# 2. Dependências
python -c "import RNA, numpy, openpyxl, Bio, customtkinter, pptx, matplotlib; print('dependencies OK')"

# 3. Testes (inclui a confirmação de que o dobramento local reproduz exatamente o servidor RNAfold)
python -m pytest -q tests

# 4. Análise completa do exemplo incluído
python -m RnaThermofinder analyze Examples/sample_dataset.fasta --out-dir ./rsas_check
```

Resultados esperados:

| Verificação | Esperado |
|---|---|
| 1 | `RSAS 4.0.0 \| ViennaRNA 2.7.x \| Python 3.1x.x` |
| 2 | `dependencies OK` |
| 3 | `71 passed` (ou mais) |
| 4 | Uma pasta `rsas_check/sample_dataset_<data_hora>/` com `sample_dataset_rna_results.csv`, `…_rna_results.xlsx`, `…_run_log.txt` e `…_run_info.json` |

Por fim, abra a interface com `python main.py`. A barra lateral deve mostrar nove páginas: Analyze, Results, Settings, Sequence Extractor, Synthetic Pool, RNArobo Search, Pseudoknot Finder, RNAfold Deck e About.

---

## 10. Executando o RSAS

| Tarefa | Comando |
|---|---|
| Aplicativo gráfico | `python main.py` (ou `rsas`, ou `python -m RnaThermofinder gui`) |
| Análise sem tela | `python -m RnaThermofinder analyze entrada.fasta [--out-dir PASTA] [--cores N] [--temps 25,37,42] [--hairpin terminal\|rbs_based]` |
| RNAfold Deck sem tela | `python -m RnaThermofinder deck --results RUN/entrada_rna_results.xlsx --tier "Tier 1" --fold both --temp 37 --out-dir RUN --name entrada_RNAfold_deck` |
| Versões | `python -m RnaThermofinder version` |

Depois do `pip install -e .`, o `rsas-cli` equivale a `python -m RnaThermofinder`.

**Organização dos resultados.** Cada análise cria a sua própria pasta, e todos os arquivos dela começam com o nome do arquivo de entrada (sem a extensão). Resultados anteriores nunca são sobrescritos.

```
~/RSAS/                                         # padrão; mude com --out-dir
└── minhas_sequencias_20261103_151813/
    ├── minhas_sequencias_rna_results.csv
    ├── minhas_sequencias_rna_results.xlsx      # abas: Full Sequence, Hairpin Analysis (+ Motif Matches)
    ├── minhas_sequencias_run_log.txt
    ├── minhas_sequencias_run_info.json         # entrada, versões, temperaturas, configurações
    └── minhas_sequencias_RNAfold_deck_…/       # criada pela página RNAfold Deck
```

As exportações do RNArobo e do Knotty vão para `~/RSAS/<entrada>_rnarobo_<data_hora>/` e `~/RSAS/<entrada>_knotty_<data_hora>/`. As configurações do usuário ficam em `~/.rsas/`.

Num cluster, a linha de comando roda em jobs de lote. Por exemplo, com SLURM:

```bash
#!/bin/bash
#SBATCH --job-name=rsas --cpus-per-task=8 --mem=8G --time=04:00:00
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate rsas
cd /caminho/para/RSAS
python -m RnaThermofinder analyze /caminho/para/entrada.fasta --out-dir /caminho/para/resultados --cores "$SLURM_CPUS_PER_TASK"
```

---

## 11. Gerando um aplicativo independente

Um aplicativo independente, que não precisa de Python na máquina de destino, é gerado com o PyInstaller em cada sistema operacional de destino (não há compilação cruzada):

```bash
python -m pip install -r requirements-dev.txt     # acrescenta pytest, setuptools, pyinstaller
python build_app.py
```

| Plataforma | Resultado |
|---|---|
| macOS | `dist/RSAS.app` e um `.dmg` para distribuição (RNArobo e Knotty incluídos) |
| Windows | `dist/RSAS.exe` |
| Linux | `dist/RSAS` (coloque antes as versões Linux dos programas em `bin/linux/` para incluí-las) |

O aplicativo não é notarizado pela Apple. Na primeira abertura, o macOS pode dizer que *o RSAS está danificado e não pode ser aberto*; o aplicativo não está danificado, e a [§7.4](#74-avisos-de-segurança-do-macos-gatekeeper) explica como abri-lo (Ajustes do Sistema → Privacidade e Segurança → **Abrir Mesmo Assim**, ou removendo a quarentena). No Windows, o SmartScreen pede **Mais informações → Executar assim mesmo**.

---

## 12. Atualização e desinstalação

**Atualizar:**

```bash
git pull                                          # ou baixe a nova versão
conda env update -f environment.yml --prune       # Conda (environment-windows.yml no Windows)
python -m pip install -r requirements.txt --upgrade   # venv nativo
docker build -t rsas:<nova-versão> .              # Docker
```

**Desinstalar:**

| Método | Comando |
|---|---|
| Conda | `conda deactivate && conda env remove -n rsas` |
| Nativo | Apague a pasta `.venv` dentro da pasta do RSAS |
| Docker | `docker image rm rsas:4.0.0` |

Depois, apague a pasta do RSAS. As configurações em `~/.rsas/` e os resultados em `~/RSAS/` ficam guardados até você mesmo apagá-los.

---

## 13. Solução de problemas

| Sintoma | Causa e solução |
|---|---|
| `ModuleNotFoundError: No module named 'RNA'` | O ViennaRNA não está instalado no ambiente ativo. Ative o ambiente (`conda activate rsas` ou `source .venv/bin/activate`) e rode `python -m pip install ViennaRNA` (venv) ou `conda install -c bioconda viennarna` (Conda, Linux/macOS). |
| O `pip` não encontra uma versão do ViennaRNA para o seu Python | Existem wheels do ViennaRNA para Python 3.10–3.13. Crie o ambiente com Python 3.11 ou 3.12. |
| `ModuleNotFoundError: No module named 'tkinter'` / `_tkinter` | O Python foi instalado sem Tk. Linux: instale `python3-tk` (Debian/Ubuntu), `python3-tkinter` (Fedora) ou `tk` (Arch). macOS: use o instalador do python.org ou `brew install python-tk@3.x`. Windows: execute de novo o instalador do Python, escolha *Modify* e marque *tcl/tk and IDLE*. |
| `_tkinter.TclError: no display name and no $DISPLAY environment variable` | Não há tela gráfica (sessão SSH, servidor, contêiner). Use a linha de comando, `ssh -X` ou `xvfb-run python main.py`. |
| `conda env create` falha no Windows com `viennarna ... does not exist` | Foi usado o `environment.yml` no Windows. Use o `environment-windows.yml`. |
| Os elementos da interface aparecem quebrados ou com tema errado | Foi instalado o customtkinter 6.x. Rode `python -m pip install "customtkinter>=5.2,<6"`. |
| A página RNAfold Deck mostra *RNAfold Deck needs 'pptx'* | Faltam as dependências do Deck. Rode `python -m pip install python-pptx matplotlib pillow lxml` ou atualize o ambiente Conda. |
| RNArobo Search / Pseudoknot Finder mostra uma faixa vermelha "not found" | Veja a [§8](#8-programas-opcionais-rnarobo-e-knotty). No macOS, rode os comandos `xattr` e do Rosetta. No Windows, confira se `bin\windows\` contém `rnarobo.exe`, `knotty.exe` e `simfold\`. No Linux, baixe o RNArobo e compile o Knotty em `bin/linux/` da pasta do RSAS (sem administrador). |
| macOS: *"RSAS" is damaged and can't be opened* | O aplicativo não está danificado; o macOS bloqueia programas não notarizados pela Apple. Ajustes do Sistema → Privacidade e Segurança → **Abrir Mesmo Assim**, ou `sudo xattr -cr /Applications/RSAS.app`. Todas as opções: [§7.4](#74-avisos-de-segurança-do-macos-gatekeeper). |
| macOS: *"rnarobo" cannot be opened because the developer cannot be verified* | Rode `xattr -dr com.apple.quarantine bin/macos` uma vez na pasta do RSAS, ou use **Abrir Mesmo Assim** ([§7.4](#74-avisos-de-segurança-do-macos-gatekeeper)). |
| macOS: o `xattr` responde *Operation not permitted* | Dê **Acesso Total ao Disco** ao Terminal (Ajustes do Sistema → Privacidade e Segurança), reinicie o Terminal e repita o comando ([§7.4](#74-avisos-de-segurança-do-macos-gatekeeper)). |
| O Knotty roda mas dá erro de parâmetros | Falta `simfold/params/` ao lado do executável `knotty`. Copie `bin/macos/simfold` para a mesma pasta do seu `knotty`. |
| `PermissionError` ao gravar os resultados | Não é possível gravar na pasta de saída. Escolha outra pasta com `--out-dir` ou dê permissão de escrita em `~/RSAS`. No Docker, veja a observação sobre `--user` na [§6.3](#63-executar-análises-sem-tela). |
| Docker no macOS: `cannot open display` | O XQuartz não está aberto, ou *Allow connections from network clients* está desativado. Depois de reiniciar o XQuartz, rode de novo `xhost + 127.0.0.1`. |
| Apple Silicon: um pacote Conda não é encontrado para `osx-arm64` | Crie um ambiente Intel: `CONDA_SUBDIR=osx-64 conda env create -f environment.yml`, depois `conda activate rsas && conda config --env --set subdir osx-64`. |

Se o problema continuar, abra uma *issue* e anexe a saída de `python -m RnaThermofinder version`, o seu sistema operacional, o método de instalação e o `<entrada>_run_log.txt` da análise que falhou.

---

## 14. Situação da validação deste guia

| Procedimento | Situação |
|---|---|
| `environment.yml`: resolução das dependências em linux-64, linux-aarch64, osx-64 e osx-arm64 | ✅ Verificado (ViennaRNA 2.7.2, Python 3.11) |
| `environment-windows.yml`: resolução das dependências em win-64; wheels do pip disponíveis | ✅ Verificado |
| Ambiente Conda no Linux: criação, 71 testes, análise pela linha de comando, RNAfold Deck, abertura da interface | ✅ Verificado |
| venv + pip nativo no Linux (Python 3.12): instalação, 71 testes, abertura da interface, comandos do `pip install -e .` | ✅ Verificado |
| Wheels do ViennaRNA no PyPI para Windows x64, macOS Intel/Apple Silicon, Linux x86_64/aarch64 (Python 3.10–3.13) | ✅ Verificado no PyPI |
| Instalação nativa em computadores Windows e macOS | ⏳ A confirmar pelo primeiro usuário de cada plataforma |
| `docker build` e os comandos Docker | ⏳ O Dockerfile ainda não foi construído; as imagens base não puderam ser baixadas no ambiente de validação |
| Download e compilação do RNArobo / Knotty (§8.2, §8.4) | ⏳ Comandos tirados das páginas e READMEs dos autores; ainda não executados |

Quando você confirmar um dos procedimentos pendentes na sua máquina, atualize esta tabela.
