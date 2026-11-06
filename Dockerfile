# RSAS 4.0 container: the full analysis toolkit (ViennaRNA, RSAS CLI, RNAfold Deck) on Linux.
#
#   docker build -t rsas:4.0.0 .
#   docker run --rm -v "$PWD":/data rsas:4.0.0 analyze /data/input.fasta --out-dir /data
#   docker run --rm rsas:4.0.0 version
#
# The GUI can also be displayed through X11 (see docs/INSTALL.md, "Docker").
# RNArobo and Knotty ship as macOS binaries only; to use them in the image, mount Linux builds into
# /opt/rsas/bin/linux (see docs/INSTALL.md).

ARG MICROMAMBA_VERSION=2.3.2
FROM mambaorg/micromamba:${MICROMAMBA_VERSION}

LABEL org.opencontainers.image.title="RSAS" \
      org.opencontainers.image.description="RNA Structure Analysis Suite: RNA thermometer and riboswitch analysis with ViennaRNA" \
      org.opencontainers.image.version="4.0.0" \
      org.opencontainers.image.licenses="MIT"

# Fonts and an X client stack for the optional GUI; xvfb for headless GUI tests.
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-dejavu-core libxrender1 libxext6 libx11-6 xvfb xauth \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# Python environment (ViennaRNA from bioconda), resolved from the same file as the conda install.
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml \
 && micromamba clean --all --yes

WORKDIR /opt/rsas
COPY --chown=$MAMBA_USER:$MAMBA_USER . /opt/rsas

# Activate the environment for the remaining RUN steps, then verify the image with the test suite.
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN python -m pip install --no-deps --no-build-isolation -e . \
 && python -m RnaThermofinder version \
 && python -m pytest -q tests

# Results go to /data when mounted; ~/RSAS otherwise.
ENV PYTHONUNBUFFERED=1 MPLBACKEND=Agg
VOLUME ["/data"]
ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python", "-m", "RnaThermofinder"]
CMD ["--help"]
