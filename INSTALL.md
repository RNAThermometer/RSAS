# Installing RSAS 4.0

This guide covers every supported way to install **RSAS (RNA Structure Analysis Suite) 4.0** on Linux, macOS and Windows: a Conda environment, a Docker image, and native Python installations for each operating system. It also covers the optional RNArobo and Knotty engines, verification, and troubleshooting.

> [!TIP]
> **Short version.** Install [Miniforge](https://github.com/conda-forge/miniforge), then run
> `conda env create -f environment.yml` (Linux/macOS) or `conda env create -f environment-windows.yml` (Windows),
> `conda activate rsas` and `python main.py`.

## Contents

1. [What gets installed](#1-what-gets-installed)
2. [Choosing an installation method](#2-choosing-an-installation-method)
3. [System requirements](#3-system-requirements)
4. [Getting the source code](#4-getting-the-source-code)
5. [Method A: Conda (recommended)](#5-method-a-conda-recommended)
6. [Method B: Docker](#6-method-b-docker)
7. [Method C: Native installation](#7-method-c-native-installation)
    - [Windows](#71-windows)
    - [macOS](#72-macos)
    - [Linux](#73-linux)
    - [macOS security warnings (Gatekeeper)](#74-macos-security-warnings-gatekeeper)
8. [Optional engines: RNArobo and Knotty](#8-optional-engines-rnarobo-and-knotty)
9. [Verifying the installation](#9-verifying-the-installation)
10. [Running RSAS](#10-running-rsas)
11. [Building a standalone application](#11-building-a-standalone-application)
12. [Updating and uninstalling](#12-updating-and-uninstalling)
13. [Troubleshooting](#13-troubleshooting)
14. [Validation status of this guide](#14-validation-status-of-this-guide)

---

## 1. What gets installed

| Component | Purpose | Source |
|---|---|---|
| **Python 3.10 – 3.13** | Runtime (3.11 recommended) | Conda, python.org, or the OS package manager |
| **ViennaRNA ≥ 2.6** | RNA folding: MFE, partition function, base-pair probabilities (Python module `RNA`) | Bioconda, or the official PyPI wheel |
| **customtkinter 5.x + Tk 8.6** | Desktop interface | PyPI / Bioconda; Tk ships with Python |
| **numpy, openpyxl, biopython** | Core analysis and Excel output | PyPI / conda-forge |
| **python-pptx, matplotlib, pillow, lxml** | RNAfold Deck: structure drawings and PowerPoint | PyPI / conda-forge |
| **RNArobo 2.1.0** *(optional)* | RNArobo Search page (structural motif search) | Bundled for macOS; Linux executable from the authors; source ([§8](#8-optional-engines-rnarobo-and-knotty)) |
| **Knotty** *(optional)* | Pseudoknot Finder page | Bundled for macOS; build from source elsewhere ([§8](#8-optional-engines-rnarobo-and-knotty)) |

RSAS needs **no internet connection and no web browser** at run time. All folding, including the RNAfold Deck structure drawings, is done locally with ViennaRNA. The only exception is the Sequence Extractor's optional *Fetch from NCBI* tab.

## 2. Choosing an installation method

| Method | Best for | Desktop GUI | Command line | RNArobo / Knotty |
|---|---|:---:|:---:|---|
| **A. Conda** | Most users, on any OS. One command, reproducible | ✅ | ✅ | macOS: bundled. Linux: build. Windows: via WSL2 |
| **B. Docker** | Servers, HPC front-ends, pipelines, reproducible batch runs | ⚠️ needs an X server | ✅ | Mount Linux builds into the container |
| **C. Native (venv + pip)** | Users without Conda, or who manage Python themselves | ✅ | ✅ | Same as Conda |

> [!NOTE]
> All three methods install the same code and the same ViennaRNA version (2.7.2 at the time of writing). Results are identical across methods and operating systems.

## 3. System requirements

| | Minimum | Recommended |
|---|---|---|
| **Operating system** | Windows 10 (64-bit), macOS 11 Big Sur, or a Linux distribution with glibc ≥ 2.24 (Ubuntu 18.04+, Debian 10+, RHEL/Rocky 8+) | Windows 11, macOS 13+, Ubuntu 22.04/24.04 |
| **CPU architecture** | x86_64, or ARM64 on macOS (Apple Silicon) and Linux | Any of these |
| **Python** | 3.10 | 3.11 or 3.12 |
| **Memory** | 4 GB | 8 GB or more for large batches and partition-function runs |
| **Disk** | 1.5 GB (Conda environment) | 3 GB |
| **Display** | Needed only for the GUI | — |

> [!WARNING]
> Windows on ARM is not supported natively because there is no ViennaRNA build for it. Use WSL2 or Docker instead.

## 4. Getting the source code

**With Git** (recommended, makes updates easy):

```bash
git clone https://github.com/<owner>/RSAS.git
cd RSAS
git checkout v4.0.0
```

Replace `<owner>` with the GitHub account that hosts your copy of RSAS.

**Without Git:** on the repository page, click **Code → Download ZIP**, extract the archive, and open a terminal in the extracted folder.

All commands below are run **from the repository root**, the folder that contains `main.py`.

---

## 5. Method A: Conda (recommended)

Conda installs Python, Tk and ViennaRNA as pre-built binaries, so no compiler and no system packages are needed. The repository provides two environment files:

| File | Platforms | ViennaRNA comes from |
|---|---|---|
| `environment.yml` | Linux (x86_64), macOS Intel, macOS Apple Silicon | Bioconda (native build) |
| `environment-windows.yml` | Windows 10/11 (x86_64) | Official PyPI wheel (Bioconda has no Windows build) |

### 5.1 Install a Conda distribution

Install **[Miniforge](https://github.com/conda-forge/miniforge)**. It is a minimal installer that uses the community `conda-forge` channel by default and includes `mamba`, a faster drop-in replacement for `conda`. Miniconda and Anaconda also work.

<details>
<summary><b>Linux / macOS</b></summary>

```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh -b -p "$HOME/miniforge3"
"$HOME/miniforge3/bin/conda" init "$(basename "$SHELL")"
# Close and reopen the terminal.
```

</details>

<details>
<summary><b>Windows</b></summary>

1. Download `Miniforge3-Windows-x86_64.exe` from the [Miniforge releases page](https://github.com/conda-forge/miniforge/releases/latest).
2. Run the installer and keep the default option *Just Me*.
3. Open **Miniforge Prompt** from the Start menu. Use this prompt for every command below.

</details>

### 5.2 Create the environment

**Linux and macOS:**

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
> Replace `conda` with `mamba` in the `env create` command for a faster solve.

The environment is named `rsas`. Activate it in every new terminal before running RSAS.

### 5.3 Install the RSAS commands (optional)

```bash
python -m pip install --no-deps -e .
```

This adds two commands to the environment: `rsas` (desktop application) and `rsas-cli` (command line). Without this step, use `python main.py` and `python -m RnaThermofinder` instead; they are equivalent.

### 5.4 Verify and run

```bash
python -m RnaThermofinder version     # RSAS 4.0.0 | ViennaRNA 2.7.2 | Python 3.11.x
python -m pytest -q tests             # all tests should pass
python main.py                        # start the desktop application
```

Continue with [§8](#8-optional-engines-rnarobo-and-knotty) if you need RNArobo Search or the Pseudoknot Finder.

---

## 6. Method B: Docker

The Docker image contains the complete Linux environment: ViennaRNA, the RSAS command line and the RNAfold Deck. The image is built from the same `environment.yml` used by Method A, and the build runs the test suite, so a successful build is a verified installation.

### 6.1 Prerequisites

- **Linux:** Docker Engine 20.10 or later ([installation instructions](https://docs.docker.com/engine/install/)). Add your user to the `docker` group, or prefix the commands below with `sudo`.
- **macOS / Windows:** [Docker Desktop](https://www.docker.com/products/docker-desktop/). On Windows, enable the WSL2 back end, which is the default.

### 6.2 Build the image

From the repository root:

```bash
docker build -t rsas:4.0.0 .
```

The build takes several minutes: it downloads the Conda packages and runs the test suite. Every dependency is available for both `linux/amd64` and `linux/arm64`, so Docker builds a native image on Intel/AMD machines and on Apple Silicon alike.

### 6.3 Run analyses (no display needed)

The container's entry point is the RSAS command line (`python -m RnaThermofinder`). Mount the folder that holds your input files as `/data`, and write results back to it:

**Linux / macOS:**

```bash
docker run --rm -v "$PWD":/data rsas:4.0.0 version
docker run --rm -v "$PWD":/data rsas:4.0.0 analyze /data/my_sequences.fasta --out-dir /data --cores 4
```

**Windows (PowerShell):**

```powershell
docker run --rm -v "${PWD}:/data" rsas:4.0.0 analyze /data/my_sequences.fasta --out-dir /data --cores 4
```

Each analysis creates a new folder, `my_sequences_<YYYYmmdd_HHMMSS>/`, next to the input file. Every file inside starts with the input's name. Build an RNAfold Deck from that run as follows (replace `<run>` with the folder name):

```bash
docker run --rm -v "$PWD":/data rsas:4.0.0 deck \
  --results "/data/<run>/my_sequences_rna_results.xlsx" \
  --tier "Tier 1" --fold both --temp 25 --temp 37 --temp 42 \
  --out-dir "/data/<run>" --name my_sequences_RNAfold_deck
```

> [!NOTE]
> Files written by the container belong to the container user (UID 57439). On Linux, add `--user "$(id -u):$(id -g)" -e HOME=/tmp` to `docker run` so the results belong to you.

Analysis settings saved by the GUI (output columns, scoring profiles, temperatures) live in `~/.rsas/` inside the container. To reuse your own settings, mount your folder: `-v "$HOME/.rsas":/home/mambauser/.rsas`.

### 6.4 Run the desktop GUI from the container (optional)

The GUI needs an X11 display. For daily GUI use, Methods A and C are simpler. Docker is mainly intended for headless work.

<details>
<summary><b>Linux (X11 or XWayland)</b></summary>

```bash
xhost +local:docker
docker run --rm -it -e DISPLAY="$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD":/data rsas:4.0.0 gui
xhost -local:docker
```

</details>

<details>
<summary><b>macOS (XQuartz)</b></summary>

1. Install [XQuartz](https://www.xquartz.org/) and log out and back in.
2. In **XQuartz → Settings → Security**, enable *Allow connections from network clients*, then restart XQuartz.
3. Run:

```bash
xhost + 127.0.0.1
docker run --rm -it -e DISPLAY=host.docker.internal:0 -v "$PWD":/data rsas:4.0.0 gui
```

</details>

<details>
<summary><b>Windows 11 (WSLg)</b></summary>

From an Ubuntu (WSL2) terminal with Docker Desktop's WSL integration enabled:

```bash
docker run --rm -it -e DISPLAY="$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /mnt/wslg:/mnt/wslg -v "$PWD":/data rsas:4.0.0 gui
```

</details>

---

## 7. Method C: Native installation

A native installation uses a standard Python virtual environment (`venv`) and `pip`. ViennaRNA is installed from its official PyPI wheel, available for Python 3.10–3.13 on Windows x64, macOS (Intel and Apple Silicon) and Linux (x86_64 and aarch64). No compiler is needed.

### 7.1 Windows

**Step 1. Install Python.** Download **Python 3.11 or 3.12 (64-bit)** from [python.org](https://www.python.org/downloads/windows/). In the installer:
- tick **Add python.exe to PATH**;
- keep **tcl/tk and IDLE** selected (required for the GUI).

**Step 2. Open PowerShell in the RSAS folder** (in File Explorer, *Shift + right-click → Open in Terminal*) and create the environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> [!NOTE]
> If PowerShell refuses to run `Activate.ps1`, allow local scripts once with
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use Command Prompt and run `.venv\Scripts\activate.bat`.

**Step 3. Verify and run:**

```powershell
python -m RnaThermofinder version
python main.py
```

**RNArobo and Knotty on Windows.** Neither engine has a native Windows build. Every other page works natively. For those two pages, run RSAS inside **WSL2** (Ubuntu) by following the [Linux instructions](#73-linux) and [§8.2](#82-linux-and-wsl2). Windows 11 shows Linux GUI applications from WSL2 directly.

### 7.2 macOS

**Step 1. Install Python 3.11 or 3.12** from [python.org](https://www.python.org/downloads/macos/). The *universal2* installer runs natively on both Intel and Apple Silicon and includes a working Tk. After installing, double-click **Install Certificates.command** in `/Applications/Python 3.x/`.

> [!WARNING]
> Avoid Apple's `/usr/bin/python3` (Command Line Tools). Its Tk is outdated and the GUI renders incorrectly. If you prefer Homebrew Python, also install its Tk bindings, for example `brew install python@3.12 python-tk@3.12`.

**Step 2. Create the environment** (Terminal, in the RSAS folder):

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Step 3. Verify and run:**

```bash
python -m RnaThermofinder version
python main.py
```

RNArobo and Knotty are bundled for macOS; see [§8.1](#81-macos-bundled) for the one-time setup. If macOS reports that RSAS or one of these programs *is damaged* or *cannot be verified*, see [§7.4](#74-macos-security-warnings-gatekeeper).

### 7.3 Linux

**Step 1. Install Python with Tk and venv support.**

| Distribution | Command |
|---|---|
| Ubuntu / Debian | `sudo apt update && sudo apt install -y python3 python3-venv python3-pip python3-tk` |
| Fedora / RHEL / Rocky / Alma | `sudo dnf install -y python3 python3-pip python3-tkinter` |
| openSUSE | `sudo zypper install -y python3 python3-pip python3-tk` |
| Arch / Manjaro | `sudo pacman -S --needed python python-pip tk` |

Check that the system Python is 3.10 or later (`python3 --version`). On older distributions (for example RHEL 8 or Ubuntu 20.04), install a newer Python, such as `python3.11` from the distribution's extra repositories, or use [Method A](#5-method-a-conda-recommended).

**Step 2. Create the environment** (in the RSAS folder):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Step 3. Verify and run:**

```bash
python -m RnaThermofinder version
python main.py
```

On headless servers, use the [command line](#10-running-rsas) only; no display is required. To run the GUI on a server, use SSH X forwarding (`ssh -X`) or a virtual display (`xvfb-run python main.py`).

### 7.4 macOS security warnings (Gatekeeper)

RSAS is academic software and is not notarized by Apple. When you open the packaged **RSAS.app** (from the `.dmg` release) or when RSAS runs the bundled **`rnarobo`** and **`knotty`** executables in `bin/macos/`, macOS may refuse with one of these messages:

- *"RSAS" is damaged and can't be opened. You should move it to the Trash.*
- *"RSAS" can't be opened because Apple cannot check it for malicious software.*
- *"rnarobo" cannot be opened because the developer cannot be verified.*

**The files are not damaged.** macOS marks every file downloaded from the internet with a `com.apple.quarantine` attribute. When a quarantined program is opened, **Gatekeeper** checks whether it is signed and notarized by Apple; if it is not, macOS blocks it and shows the (misleading) "damaged" message. Use the solutions below in order, and only for copies of RSAS downloaded from the official repository.

**Solution 1. Allow it in System Settings (recommended, safest).**

1. Open RSAS once; when the error appears, click **Cancel** (or **Done**).
2. Open **System Settings → Privacy & Security**.
3. Scroll down to **Security**. A message says that "RSAS" (or "rnarobo" / "knotty") was blocked because it is not from an identified developer.
4. Click **Open Anyway** and enter your Mac password. RSAS opens, and macOS remembers the choice.

On macOS 15 (Sequoia) and later, right-click → **Open** no longer bypasses this check; use **Open Anyway** as above.

**Solution 2. Remove the quarantine flag in Terminal** (if **Open Anyway** does not appear):

```bash
# The application installed in /Applications
sudo xattr -cr /Applications/RSAS.app

# The RNArobo and Knotty executables in your RSAS folder (no sudo needed: it is your own folder)
cd /path/to/RSAS
xattr -dr com.apple.quarantine bin/macos
chmod +x bin/macos/rnarobo bin/macos/knotty
```

Tip: type `sudo xattr -cr ` (with a trailing space) and drag **RSAS.app** from Finder into the Terminal window to fill in its path. Then open RSAS again. If the "damaged" message still appears, go to **System Settings → Privacy & Security**, where **Open Anyway** should now be available (Solution 1, steps 3–4).

The DMG also contains **Install RSAS.sh**, which copies RSAS.app to `/Applications` and removes the quarantine flag in one step.

*If Terminal reports "Operation not permitted"*, it lacks permission to change the file:

1. Open **System Settings → Privacy & Security → Full Disk Access**.
2. Unlock if needed, click **+**, choose **Applications → Utilities → Terminal.app**, and turn its switch on.
3. Quit Terminal completely, open it again, and rerun the `xattr` command.

**Solution 3. Temporarily disable Gatekeeper** (if the commands above fail). Re-enable it immediately after RSAS has opened once:

```bash
sudo spctl --master-disable     # recent macOS versions also ask you to confirm in Privacy & Security ("Anywhere")
open /Applications/RSAS.app
sudo spctl --master-enable      # turn Gatekeeper back on right away
```

**Solution 4. Ad-hoc code signing** (last resort). Sign the program locally with an ad-hoc signature:

```bash
sudo codesign --force --deep --sign - /Applications/RSAS.app
codesign --force --sign - bin/macos/rnarobo bin/macos/knotty      # from your RSAS folder
```

| Step | Method | When to use it |
|---|---|---|
| 1 | System Settings → Privacy & Security → **Open Anyway** | First choice; safest |
| 2 | `xattr` (remove quarantine), then **Open Anyway** | **Open Anyway** is not offered at first; also the standard one-time step for `bin/macos/` |
| 3 | Disable Gatekeeper temporarily | The Terminal commands fail; re-enable immediately |
| 4 | Ad-hoc code signing | Last resort |

Running RSAS from source (Conda or `python main.py`) does not trigger these warnings for RSAS itself, because Python is already trusted; only the `rnarobo` and `knotty` executables in `bin/macos/` need Solution 2 once.

---

## 8. Optional engines: RNArobo and Knotty

Only two pages depend on external executables: **RNArobo Search** (`rnarobo`) and **Pseudoknot Finder** (`knotty`). Everything else, including the main analysis and the RNAfold Deck, works without them.

> [!NOTE]
> **No administrator rights are needed.** `bin/` below always means the `bin/` folder **inside your RSAS folder** (for example `~/RSAS/bin/linux/`), not a system folder such as `/usr/bin`. Every command in this section writes only to your RSAS folder or to a temporary folder.

RSAS looks for each executable in this order:

1. inside the packaged application (PyInstaller build);
2. `bin/<platform>/` in your RSAS folder: `bin/macos/`, `bin/linux/` or `bin/windows/`;
3. the `PATH` (a user-owned folder on the `PATH`, such as `~/.local/bin`, also works).

Knotty also needs its energy parameter folder, `simfold/`, next to the `knotty` executable. Each page shows a green banner with the path of the engine when it is found.

| Engine | Authors and source | License | Reference |
|---|---|---|---|
| **RNArobo 2.1.0** | Computational Biology, Comenius University in Bratislava: <https://compbio.fmph.uniba.sk/software.php> (newest version: <https://github.com/rampasek/RNArobo>) | GPL-3.0 | Rampášek L, Jimenez RM, Lupták A, Vinař T, Brejová B. *RNA motif search with data-driven element ordering.* BMC Bioinformatics 17:216 (2016) |
| **Knotty** | Hosna Jabbari, University of Alberta: <https://github.com/HosnaJabbari/Knotty> (energy parameters from SimFold/MultiRNAFold) | GPL | Jabbari H, Wark I, Montemagno C, Will S. *Knotty: efficient and accurate prediction of complex RNA pseudoknot structures.* Bioinformatics 34:3849–3856 (2018) |

In the commands below, replace `/path/to/RSAS` with your RSAS folder (the folder that contains `main.py`).

### 8.1 macOS (bundled)

Both executables ship in `bin/macos/` together with Knotty's parameters. They are Intel (x86_64) builds:

```bash
cd /path/to/RSAS

# Apple Silicon only: install Rosetta 2 once
softwareupdate --install-rosetta --agree-to-license

# Remove the download quarantine flag so macOS lets the binaries run
xattr -dr com.apple.quarantine bin/macos
chmod +x bin/macos/rnarobo bin/macos/knotty
```

If macOS still blocks `rnarobo` or `knotty` (*cannot be opened because the developer cannot be verified*), allow them in **System Settings → Privacy & Security → Open Anyway**, or follow the other solutions in [§7.4](#74-macos-security-warnings-gatekeeper).

To use native Apple Silicon builds instead, build both engines from source ([§8.4](#84-building-from-source-macos-and-linux)) and copy them into `bin/macos/`, replacing the bundled files.

### 8.2 Linux and WSL2

**RNArobo: download the ready-made Linux executable** (64-bit) published by its authors, straight into your RSAS folder:

```bash
cd /path/to/RSAS
mkdir -p bin/linux
curl -L -o bin/linux/rnarobo https://compbio.fmph.uniba.sk/rnarobo/rnarobo-2.1.0-linux64
#   (or: wget -O bin/linux/rnarobo https://compbio.fmph.uniba.sk/rnarobo/rnarobo-2.1.0-linux64)
chmod +x bin/linux/rnarobo
bin/linux/rnarobo 2>&1 | head -n 5          # prints its usage
```

If this executable does not run on your distribution, build RNArobo from source ([§8.4.1](#841-rnarobo-from-source)).

**Knotty: build it from source** and install it in `bin/linux/` ([§8.4.2](#842-knotty-from-source)). No ready-made Linux executable is published.

**Docker.** To use the engines inside the container, mount the folder that contains `rnarobo`, `knotty` and `simfold/`:

```bash
docker run --rm -it -v "$PWD/bin/linux":/opt/rsas/bin/linux ... rsas:4.0.0 gui
```

### 8.3 Windows

Neither engine has a native Windows build. Run RSAS inside **WSL2** (Ubuntu) for these two pages ([§7.1](#71-windows)) and follow §8.2 inside WSL2. Advanced users who compile `rnarobo.exe` / `knotty.exe` themselves (for example with MSYS2) can place them in `bin\windows\`, with Knotty's `simfold\` folder next to `knotty.exe`.

### 8.4 Building from source (macOS and Linux)

You need a C/C++ compiler and `make`:

| System | Command (once) |
|---|---|
| macOS | `xcode-select --install` (Apple Command Line Tools) |
| Debian / Ubuntu / WSL2 | `sudo apt install -y build-essential` |
| Fedora / RHEL / Rocky | `sudo dnf install -y gcc gcc-c++ make` |

On a shared server without administrator rights, the compilers are usually already installed (`gcc --version`), or available as a module (`module load gcc`).

Set two variables for the commands below (`PLAT` is `macos` or `linux`):

```bash
RSAS=/path/to/RSAS
PLAT=linux                       # or: PLAT=macos
mkdir -p "$RSAS/bin/$PLAT"
```

#### 8.4.1 RNArobo from source

From the release archive (RNArobo 2.1.0):

```bash
cd /tmp
curl -LO https://compbio.fmph.uniba.sk/rnarobo/rnarobo-2.1.0.tar.gz
tar -zxf rnarobo-2.1.0.tar.gz
cd rnarobo-2.1.0
make
cp rnarobo "$RSAS/bin/$PLAT/"
chmod +x "$RSAS/bin/$PLAT/rnarobo"
```

or from the newest version on GitHub:

```bash
cd /tmp
git clone https://github.com/rampasek/RNArobo.git
cd RNArobo
make
cp rnarobo "$RSAS/bin/$PLAT/"
```

The RNArobo manual (descriptor format) is at <https://compbio.fmph.uniba.sk/rnarobo/rnarobo-readme.pdf>.

#### 8.4.2 Knotty from source

Knotty needs a compiler that supports C++11 (g++ 4.7.2 or later, or Apple clang) and **CMake 3.1 or later**. Check with `cmake --version`. If CMake is missing or older, install it with any of:

```bash
conda install -n rsas -c conda-forge cmake      # inside the RSAS Conda environment (no administrator rights)
python -m pip install --user cmake              # any Python, user install (no administrator rights)
brew install cmake                              # macOS with Homebrew (https://brew.sh)
sudo apt install -y cmake                       # Debian / Ubuntu / WSL2
```

Download, build and install Knotty. Build it in a folder you keep (here `~/tools/Knotty-master`), because Knotty's authors note that its `simfold/` folder must not be deleted or moved after compiling:

```bash
mkdir -p ~/tools && cd ~/tools
curl -L -o Knotty-master.zip https://github.com/HosnaJabbari/Knotty/archive/master.zip
unzip -q Knotty-master.zip
cd Knotty-master                 # the folder that contains Knotty's README.md

cmake -H. -Bbuild
cmake --build build
#   C++11 errors? Delete the build folder and specify the compiler:
#   rm -rf build && cmake -H. -Bbuild -DCMAKE_CXX_COMPILER=g++ && cmake --build build

# Install into your RSAS folder: the executable and its energy parameters, side by side
cp "$(find . -maxdepth 2 -type f -name knotty -perm -u+x | head -n 1)" "$RSAS/bin/$PLAT/"
cp -R simfold "$RSAS/bin/$PLAT/"
chmod +x "$RSAS/bin/$PLAT/knotty"
```

`git clone https://github.com/HosnaJabbari/Knotty.git` can replace the download and `unzip` lines. If you recompile after moving the Knotty folder, delete its `build/` folder first.

### 8.5 Checking the engines

```bash
cd /path/to/RSAS
python -c "from RnaThermofinder.utils.rnarobo_wrapper import check_rnarobo_available as c; print(c())"
python -c "from RnaThermofinder.utils.knotty_wrapper import check_knotty_available as c; print(c())"
(cd bin/linux && ./knotty GCAACGAUGACAUACAUCGCUAGUCGACGC -w)     # bin/macos on a Mac
```

Each `check_…` line prints `(True, '<path of the executable>')`, and the Knotty test prints a dot-bracket structure with its energy. In the application, the RNArobo Search and Pseudoknot Finder pages show a green banner.

---

## 9. Verifying the installation

Run these checks inside the activated environment, from the repository root:

```bash
# 1. Versions
python -m RnaThermofinder version

# 2. Dependencies
python -c "import RNA, numpy, openpyxl, Bio, customtkinter, pptx, matplotlib; print('dependencies OK')"

# 3. Test suite (includes a check that the local fold reproduces the RNAfold webserver exactly)
python -m pytest -q tests

# 4. End-to-end analysis of the bundled example
python -m RnaThermofinder analyze Examples/sample_dataset.fasta --out-dir ./rsas_check
```

Expected results:

| Check | Expected |
|---|---|
| 1 | `RSAS 4.0.0 \| ViennaRNA 2.7.x \| Python 3.1x.x` |
| 2 | `dependencies OK` |
| 3 | `71 passed` (or more) |
| 4 | A folder `rsas_check/sample_dataset_<timestamp>/` with `sample_dataset_rna_results.csv`, `…_rna_results.xlsx`, `…_run_log.txt` and `…_run_info.json` |

Finally, start the GUI with `python main.py`. The sidebar should list eight pages: Analyze, Results, Settings, Sequence Extractor, Synthetic Pool, RNArobo Search, Pseudoknot Finder and RNAfold Deck.

---

## 10. Running RSAS

| Task | Command |
|---|---|
| Desktop application | `python main.py` (or `rsas`, or `python -m RnaThermofinder gui`) |
| Analysis without a display | `python -m RnaThermofinder analyze input.fasta [--out-dir DIR] [--cores N] [--temps 25,37,42] [--hairpin terminal\|rbs_based]` |
| RNAfold Deck without a display | `python -m RnaThermofinder deck --results RUN/input_rna_results.xlsx --tier "Tier 1" --fold both --temp 37 --out-dir RUN --name input_RNAfold_deck` |
| Versions | `python -m RnaThermofinder version` |

`rsas-cli` is equivalent to `python -m RnaThermofinder` after `pip install -e .`.

**Output layout.** Every analysis creates its own folder, and every file in it starts with the input file's name (without the extension). Earlier results are never overwritten.

```
~/RSAS/                                   # default; change with --out-dir
└── my_sequences_20261103_151813/
    ├── my_sequences_rna_results.csv
    ├── my_sequences_rna_results.xlsx     # tabs: Full Sequence, Hairpin Analysis (+ Motif Matches)
    ├── my_sequences_run_log.txt
    ├── my_sequences_run_info.json        # input, versions, temperatures, settings
    └── my_sequences_RNAfold_deck_…/      # created by the RNAfold Deck page
```

RNArobo and Knotty exports go to `~/RSAS/<input>_rnarobo_<timestamp>/` and `~/RSAS/<input>_knotty_<timestamp>/`. User settings are stored in `~/.rsas/`.

On a cluster, the command line runs in batch jobs. For example, with SLURM:

```bash
#!/bin/bash
#SBATCH --job-name=rsas --cpus-per-task=8 --mem=8G --time=04:00:00
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate rsas
cd /path/to/RSAS
python -m RnaThermofinder analyze /path/to/input.fasta --out-dir /path/to/results --cores "$SLURM_CPUS_PER_TASK"
```

---

## 11. Building a standalone application

A self-contained application, which needs no Python on the target machine, is built with PyInstaller on each target operating system (cross-compilation is not supported):

```bash
python -m pip install -r requirements-dev.txt     # adds pytest, setuptools, pyinstaller
python build_app.py
```

| Platform | Output |
|---|---|
| macOS | `dist/RSAS.app` and a distributable `.dmg` (RNArobo and Knotty included) |
| Windows | `dist/RSAS.exe` |
| Linux | `dist/RSAS` (place Linux builds of the engines in `bin/linux/` first to include them) |

The application is not notarized by Apple. On first launch, macOS may report that *RSAS is damaged and can't be opened*; the app is not damaged, and [§7.4](#74-macos-security-warnings-gatekeeper) explains how to open it (System Settings → Privacy & Security → **Open Anyway**, or removing the quarantine flag). Windows SmartScreen requires **More info → Run anyway**.

---

## 12. Updating and uninstalling

**Update:**

```bash
git pull                                   # or download the new release
conda env update -f environment.yml --prune      # Conda (environment-windows.yml on Windows)
python -m pip install -r requirements.txt --upgrade   # native venv
docker build -t rsas:<new-version> .              # Docker
```

**Uninstall:**

| Method | Command |
|---|---|
| Conda | `conda deactivate && conda env remove -n rsas` |
| Native | Delete the `.venv` folder in the RSAS directory |
| Docker | `docker image rm rsas:4.0.0` |

Then delete the RSAS folder. User settings in `~/.rsas/` and results in `~/RSAS/` are kept until you delete them yourself.

---

## 13. Troubleshooting

| Symptom | Cause and solution |
|---|---|
| `ModuleNotFoundError: No module named 'RNA'` | ViennaRNA is not installed in the active environment. Activate it (`conda activate rsas` or `source .venv/bin/activate`) and run `python -m pip install ViennaRNA` (venv) or `conda install -c bioconda viennarna` (Conda, Linux/macOS). |
| `pip` cannot find a ViennaRNA version for your Python | ViennaRNA wheels exist for Python 3.10–3.13. Create the environment with Python 3.11 or 3.12. |
| `ModuleNotFoundError: No module named 'tkinter'` / `_tkinter` | Python was installed without Tk. Linux: install `python3-tk` (Debian/Ubuntu), `python3-tkinter` (Fedora) or `tk` (Arch). macOS: use the python.org installer or `brew install python-tk@3.x`. Windows: rerun the Python installer, choose *Modify*, and tick *tcl/tk and IDLE*. |
| `_tkinter.TclError: no display name and no $DISPLAY environment variable` | No graphical display (SSH session, server, container). Use the command line, `ssh -X`, or `xvfb-run python main.py`. |
| `conda env create` fails on Windows with `viennarna ... does not exist` | `environment.yml` was used on Windows. Use `environment-windows.yml`. |
| GUI widgets look broken or the theme is wrong | customtkinter 6.x was installed. Run `python -m pip install "customtkinter>=5.2,<6"`. |
| *RNAfold Deck needs 'pptx'* is shown on the RNAfold Deck page | Deck dependencies are missing. Run `python -m pip install python-pptx matplotlib pillow lxml`, or update the Conda environment. |
| RNArobo Search / Pseudoknot Finder shows a red "not found" banner | See [§8](#8-optional-engines-rnarobo-and-knotty). On macOS, run the `xattr` and Rosetta commands. On Linux, download RNArobo and build Knotty into `bin/linux/` of your RSAS folder (no administrator rights needed). |
| macOS: *"RSAS" is damaged and can't be opened* | The app is not damaged; macOS blocks programs that are not notarized by Apple. System Settings → Privacy & Security → **Open Anyway**, or `sudo xattr -cr /Applications/RSAS.app`. All options: [§7.4](#74-macos-security-warnings-gatekeeper). |
| macOS: *"rnarobo" cannot be opened because the developer cannot be verified* | Run `xattr -dr com.apple.quarantine bin/macos` once in your RSAS folder, or use **Open Anyway** ([§7.4](#74-macos-security-warnings-gatekeeper)). |
| macOS: `xattr` reports *Operation not permitted* | Give Terminal **Full Disk Access** (System Settings → Privacy & Security), restart Terminal and run the command again ([§7.4](#74-macos-security-warnings-gatekeeper)). |
| Knotty runs but returns an error about parameters | `simfold/params/` is missing next to the `knotty` executable. Copy `bin/macos/simfold` to the same folder as your `knotty`. |
| `PermissionError` when writing results | The output folder is not writable. Choose another folder with `--out-dir`, or make `~/RSAS` writable. In Docker, see the `--user` note in [§6.3](#63-run-analyses-no-display-needed). |
| Docker on macOS: `cannot open display` | XQuartz is not running, or *Allow connections from network clients* is off. Rerun `xhost + 127.0.0.1` after restarting XQuartz. |
| Apple Silicon: a Conda package is not found for `osx-arm64` | Create an Intel environment instead: `CONDA_SUBDIR=osx-64 conda env create -f environment.yml`, then `conda activate rsas && conda config --env --set subdir osx-64`. |

If a problem persists, open an issue and attach the output of `python -m RnaThermofinder version`, your operating system, the installation method, and the `<input>_run_log.txt` of the failing run.

---

## 14. Validation status of this guide

| Procedure | Status |
|---|---|
| `environment.yml`: dependency resolution on linux-64, linux-aarch64, osx-64 and osx-arm64 | ✅ Verified (ViennaRNA 2.7.2, Python 3.11) |
| `environment-windows.yml`: dependency resolution on win-64; pip wheels available | ✅ Verified |
| Conda environment on Linux: creation, 71 tests, CLI analysis, RNAfold Deck, GUI start (8 pages) | ✅ Verified |
| Native venv + pip on Linux (Python 3.12): installation, 71 tests, GUI start, `pip install -e .` commands | ✅ Verified |
| ViennaRNA PyPI wheels for Windows x64, macOS Intel/Apple Silicon, Linux x86_64/aarch64 (Python 3.10–3.13) | ✅ Verified on PyPI |
| Native installation run on Windows and macOS hardware | ⏳ To be confirmed by the first user on each platform |
| `docker build` and the Docker commands | ⏳ The Dockerfile has not yet been built; base images could not be pulled in the validation environment |
| RNArobo / Knotty downloads and builds (§8.2, §8.4) | ⏳ Commands taken from the authors' pages and READMEs; not yet run |

When you confirm one of the pending procedures on your machine, please update this table.
