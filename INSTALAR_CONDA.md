# Instalação rápida (Conda) — RSAS 4.0

O guia completo, em inglês, está em **[INSTALL.md](INSTALL.md)**: Conda, Docker e instalação nativa em Windows, macOS e Linux, RNArobo/Knotty, verificação e solução de problemas.

```bash
# Linux e macOS (Intel e Apple Silicon)
conda env create -f environment.yml
# Windows (Miniforge Prompt)
conda env create -f environment-windows.yml

conda activate rsas
python -m RnaThermofinder version      # RSAS 4.0.0 | ViennaRNA 2.7.x
python -m pytest -q tests
python main.py                         # interface gráfica
python -m RnaThermofinder analyze arquivo.fasta --out-dir resultados   # linha de comando
```

- Cada análise cria a pasta `~/RSAS/<arquivo>_<AAAAMMDD_HHMMSS>/`, e todos os arquivos começam com o nome do FASTA de entrada.
- RNArobo e Knotty (opcionais; só as páginas RNArobo Search e Pseudoknot Finder precisam deles) são instalados **dentro da pasta do RSAS** (`bin/<plataforma>/`), sem permissão de administrador. No macOS já vêm em `bin/macos/` (rode uma vez `xattr -dr com.apple.quarantine bin/macos`; no Apple Silicon, instale o Rosetta 2). No Windows, use WSL2 e siga os passos do Linux.

### RNArobo e Knotty no Linux e WSL2

Na pasta do RSAS:

```bash
# RNArobo 2.1.0: executável pronto para Linux, dos autores (Comenius University in Bratislava)
mkdir -p bin/linux
curl -L -o bin/linux/rnarobo https://compbio.fmph.uniba.sk/rnarobo/rnarobo-2.1.0-linux64
chmod +x bin/linux/rnarobo

# Knotty: compilar do código-fonte (precisa de compilador C++11 e CMake >= 3.1)
conda install -n rsas -c conda-forge cmake          # se `cmake --version` não mostrar 3.1 ou mais
RSAS="$PWD"
mkdir -p ~/tools && cd ~/tools                      # pasta permanente: o simfold/ não deve ser movido após compilar
curl -L -o Knotty-master.zip https://github.com/HosnaJabbari/Knotty/archive/master.zip
unzip -q Knotty-master.zip && cd Knotty-master
cmake -H. -Bbuild && cmake --build build            # erro de C++11? use -DCMAKE_CXX_COMPILER=g++
cp "$(find . -maxdepth 2 -type f -name knotty -perm -u+x | head -n 1)" "$RSAS/bin/linux/"
cp -R simfold "$RSAS/bin/linux/"                    # parâmetros de energia, ao lado do executável
cd "$RSAS"

# Verificar
(cd bin/linux && ./knotty GCAACGAUGACAUACAUCGCUAGUCGACGC -w)
bin/linux/rnarobo 2>&1 | head -n 5
```

Compilação no macOS, RNArobo a partir do código-fonte, Docker e verificação: seção 8 do [INSTALL.md](INSTALL.md#8-optional-engines-rnarobo-and-knotty).

### macOS: “RSAS está danificado e não pode ser aberto”

O RSAS não é notarizado pela Apple. Por isso o macOS pode bloquear o **RSAS.app** baixado, ou os programas `rnarobo` e `knotty` de `bin/macos/`, com a mensagem *"is damaged and can't be opened"* ou *"cannot be verified"*. **O arquivo não está danificado**: o macOS marca tudo o que vem da internet com o atributo `com.apple.quarantine`, e o Gatekeeper bloqueia programas sem notarização. Use as soluções na ordem:

1. **Liberar em Ajustes do Sistema (recomendado).** Clique em **Cancelar**, abra **Ajustes do Sistema → Privacidade e Segurança**, role até **Segurança**, clique em **Abrir Mesmo Assim** (*Open Anyway*) e digite sua senha. No macOS 15 (Sequoia) ou mais novo, o clique direito → **Abrir** não funciona mais para isso.
2. **Remover a quarentena no Terminal** (se o botão não aparecer):

   ```bash
   sudo xattr -cr /Applications/RSAS.app            # o aplicativo instalado
   cd /caminho/para/RSAS
   xattr -dr com.apple.quarantine bin/macos         # RNArobo e Knotty (pasta sua, sem sudo)
   ```

   Dica: digite `sudo xattr -cr ` (com espaço no fim) e arraste o RSAS.app do Finder para o Terminal. Depois tente abrir de novo e, se ainda aparecer "danificado", use **Abrir Mesmo Assim** (passo 1). O DMG também traz o **Install RSAS.sh**, que copia o app para `/Applications` e remove a quarentena.

   Se aparecer *Operation not permitted*: **Ajustes do Sistema → Privacidade e Segurança → Acesso Total ao Disco**, clique em **+**, escolha **Aplicativos → Utilitários → Terminal.app**, ative a chave, feche e reabra o Terminal e rode o comando de novo.
3. **Desativar o Gatekeeper temporariamente** (se os comandos falharem). Reative logo depois de abrir o RSAS:

   ```bash
   sudo spctl --master-disable      # versões recentes pedem confirmação em Privacidade e Segurança ("Qualquer lugar")
   open /Applications/RSAS.app
   sudo spctl --master-enable       # reative imediatamente
   ```
4. **Assinatura ad hoc** (último recurso):

   ```bash
   sudo codesign --force --deep --sign - /Applications/RSAS.app
   codesign --force --sign - bin/macos/rnarobo bin/macos/knotty
   ```

Detalhes em inglês: seção 7.4 do [INSTALL.md](INSTALL.md#74-macos-security-warnings-gatekeeper).
