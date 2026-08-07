# Installation

This guide installs `acc-source-docs-processor` from GitHub on Windows, Linux,
or macOS. It covers both command-line use and the optional local Streamlit
interface.

All commands after downloading the repository must be run from the project root,
the directory containing `main.py`, `streamlit_app.py`, and the requirements
files.

## 1. Requirements

The application requires:

- Python 3.10 or newer;
- Tesseract OCR with English and Russian language data for image workflows and
  scanned-PDF fallback;
- Git when cloning the repository from the command line;
- enough local disk space for source documents, generated output, and the Python
  virtual environment.

The application is local. It does not require a cloud account or remote storage.

## 2. Copy the project to the local computer

### Option A: clone with Git

Open the repository page on GitHub, select **Code**, copy the HTTPS clone URL,
then run:

```bash
git clone <repository-url>
cd acc-source-docs-processor
```

Replace `<repository-url>` with the URL copied from GitHub.

### Option B: download a ZIP archive

On the GitHub repository page:

1. select **Code**;
2. select **Download ZIP**;
3. extract the archive to a normal local folder;
4. open a terminal in the extracted `acc-source-docs-processor` folder.

Do not run the application directly from inside the compressed ZIP archive.

## 3. Install system prerequisites

### Windows

1. Install a 64-bit Python version 3.10 or newer. Enable the Python launcher
   (`py`) during installation.
2. Install Git for Windows when using `git clone`.
3. Install a recent 64-bit Tesseract build. The Tesseract project documentation
   lists the Windows builds maintained by UB Mannheim because current Tesseract
   releases do not provide an official Windows installer.
4. Ensure English and Russian language data are installed.
5. Add the Tesseract installation directory to `PATH`. A common location is:

```text
C:\Program Files\Tesseract-OCR
```

Open a new PowerShell or Command Prompt window after changing `PATH`.

Verify the prerequisites:

```powershell
py --version
tesseract --version
tesseract --list-langs
```

The language list must contain at least `eng` and `rus`.

### Ubuntu / Debian Linux

Install Python, virtual-environment support, Git, Tesseract, and its English and
Russian language packages:

```bash
sudo apt-get update
sudo apt-get install -y \
  git \
  python3 \
  python3-pip \
  python3-venv \
  tesseract-ocr \
  tesseract-ocr-eng \
  tesseract-ocr-rus
```

Verify the prerequisites:

```bash
python3 --version
tesseract --version
tesseract --list-langs
```

The installed Python must be version 3.10 or newer, and the Tesseract language
list must contain `eng` and `rus`.

Other Linux distributions should use their package manager to install the same
components.

### macOS

The following commands use Homebrew:

```bash
brew install python git tesseract tesseract-lang
```

Verify the prerequisites:

```bash
python3 --version
tesseract --version
tesseract --list-langs
```

The installed Python must be version 3.10 or newer, and the Tesseract language
list must contain `eng` and `rus`.

## 4. Create a Python virtual environment

A virtual environment keeps application packages separate from the global Python
installation.

### Windows PowerShell

From the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

When PowerShell blocks the activation script, use Command Prompt instead:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
```

Activation is optional. Commands can also use the virtual-environment interpreter
directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

### Linux and macOS

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 5. Install application dependencies

Choose one installation profile.

### Command-line application only

```bash
python -m pip install -r requirements.txt
```

### Command-line application and Streamlit UI

`requirements-ui.txt` already includes the normal runtime dependencies:

```bash
python -m pip install -r requirements-ui.txt
```

### Development and tests

Install the test dependencies and the optional UI dependencies when the complete
suite or UI tests will be run:

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-ui.txt
```

## 6. Install the Russian spaCy model

The `automatic` and `combined` anonymization modes use the Russian spaCy model
through local Presidio analysis:

```bash
python -m spacy download ru_core_news_sm
```

The `configured` and `disabled` modes do not load Presidio or spaCy. Legacy
configuration files without `entityDetectionMode` retain their previous
behavior: non-empty `included` or `includedAndReplaced` rules imply configured
mode; otherwise automatic mode is used. Installing the model is recommended so
all four modes remain available.

## 7. Verify the installation

Check Python imports:

```bash
python -c "import cv2, fitz, pytesseract, spacy; print('Runtime imports OK')"
```

For a UI installation, also check Streamlit:

```bash
python -m streamlit version
```

Check OCR languages again from the same terminal:

```bash
tesseract --list-langs
```

The output must include `eng` and `rus`.

## 8. Start the application

### Streamlit UI

Start the Russian interface:

```bash
python -m streamlit run streamlit_app.py -- --lang ru
```

Start the English interface:

```bash
python -m streamlit run streamlit_app.py -- --lang en
```

Streamlit starts a local server and normally opens the interface in the default
browser. Stop it with `Ctrl+C` in the terminal.

The UI reads and writes local filesystem paths. It is designed for localhost use
on the same machine that stores the documents.

### Command-line interface

Display the available commands:

```bash
python main.py --help
python main.py process --help
python main.py anonymize --help
```

See [Usage](USAGE.md) for complete examples.

## 9. Update an existing installation

When the project was cloned with Git:

```bash
git pull
```

Activate the existing virtual environment, then refresh dependencies:

```bash
python -m pip install -r requirements-ui.txt
python -m spacy download ru_core_news_sm
```

Use `requirements.txt` instead when the installation intentionally excludes the
Streamlit UI.

For ZIP-based installations, download the new archive, extract it into a new
folder, and recreate or reuse a virtual environment deliberately. Do not overwrite
private input, output, or configuration folders stored outside the repository.

## Troubleshooting

### `tesseract` is not recognized or not found

Tesseract is either not installed or its executable directory is not in `PATH`.
On Windows, add the Tesseract installation directory to `PATH` and open a new
terminal. On Linux and macOS, confirm that the package-manager installation
completed successfully.

### Russian OCR is unavailable

Run:

```bash
tesseract --list-langs
```

Install or restore the `rus` language data when it is absent. The project uses
`rus+eng` by default for OCR-backed operations.

### `No module named streamlit`

Activate the intended virtual environment and install the UI profile:

```bash
python -m pip install -r requirements-ui.txt
```

### The Streamlit entry point cannot be found

Change to the project root before launching:

```bash
cd acc-source-docs-processor
python -m streamlit run streamlit_app.py -- --lang ru
```

### PowerShell does not activate `.venv`

Use Command Prompt with `.venv\Scripts\activate.bat`, or call
`.venv\Scripts\python.exe` directly without activation.

### OCR-dependent packages install but processing fails

Confirm that both the Python package `pytesseract` and the separate Tesseract
system application are installed. `pip install` does not install the Tesseract
executable or its language data.

## Official references

- [GitHub: cloning a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
- [Python: virtual environments](https://docs.python.org/3/library/venv.html)
- [Tesseract installation](https://tesseract-ocr.github.io/tessdoc/Installation.html)
- [Tesseract downloads and Windows builds](https://tesseract-ocr.github.io/tessdoc/Downloads.html)
- [Homebrew Tesseract formula](https://formulae.brew.sh/formula/tesseract)
- [Homebrew additional Tesseract languages](https://formulae.brew.sh/formula/tesseract-lang)
- [Streamlit command-line installation](https://docs.streamlit.io/get-started/installation/command-line)
- [Streamlit application launch](https://docs.streamlit.io/develop/concepts/architecture/run-your-app)
