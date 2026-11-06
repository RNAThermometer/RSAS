# Installation guide

The installation guide is in [INSTALL.md](../INSTALL.md) at the repository root. It covers Conda, Docker and native
installations on Windows, macOS and Linux, the optional RNArobo and Knotty engines, verification and
troubleshooting.

RNArobo and Knotty (needed only by the RNArobo Search and Pseudoknot Finder pages) are installed inside the RSAS
folder, in `bin/<platform>/`, without administrator rights: download RNArobo's ready-made Linux executable,
build Knotty from source, or use the macOS builds bundled in `bin/macos/`. Step-by-step commands are in
[INSTALL.md, section 8](../INSTALL.md#8-optional-engines-rnarobo-and-knotty).

On macOS, if RSAS.app or the bundled engines are reported as *damaged* or *cannot be verified*, they are not damaged:
macOS blocks programs that are not notarized by Apple. Allow them in System Settings → Privacy & Security →
**Open Anyway**, or remove the quarantine flag; see
[INSTALL.md, section 7.4](../INSTALL.md#74-macos-security-warnings-gatekeeper).
