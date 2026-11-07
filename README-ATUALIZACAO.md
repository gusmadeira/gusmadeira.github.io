# Atualização automática das citações — Gustavo Madeira

## Arquivos no pacote

- `publications.html`: a sua página enviada, com **cinco atributos `data-scholar-*` adicionados** à área de métricas; não alterei a lista de publicações.
- `citacoes.py`: substitui o script antigo, gera um gráfico novo e atualiza apenas as métricas de citações no HTML.
- `research/output.png`: versão redesenhada do gráfico usando **os valores que você forneceu** no `citacoes.py` anterior (NÃO é uma atualização ao vivo).
- `requirements-scholar.txt`: dependências Python.
- `.github/workflows/atualizar-citacoes.yml`: atualização semanal automática pelo GitHub Actions.

## Instalação

Copie todos os arquivos para a raiz do repositório `gusmadeira.github.io`, preservando a estrutura de pastas:

```text
gusmadeira.github.io/
├── publications.html
├── citacoes.py
├── requirements-scholar.txt
├── research/
│   └── output.png
└── .github/
    └── workflows/
        └── atualizar-citacoes.yml
```

Não altere `styles.css`, `site.js` nem os outros HTMLs.

## Testar o novo gráfico sem API

No Terminal, dentro da pasta do site:

```bash
python -m pip install -r requirements-scholar.txt
python citacoes.py --preview
```

Isso substitui **somente `research/output.png`**, usando a lista histórica de valores do seu programa. **Não** muda `publications.html` nem finge ter consultado o Scholar.

## Atualizar com dados reais do Google Scholar

O Google Scholar não possui API oficial. O script consulta a [SerpApi](https://serpapi.com/), que retorna a distribuição anual e os totais de citações para o seu Scholar ID `ZF1mcjoAAAAJ`. A SerpApi oferece uma modalidade gratuita limitada.

1. Crie uma conta em <https://serpapi.com/> e copie a API key.
2. Em seu Terminal (zsh no macOS), execute:

   ```bash
   export SERPAPI_API_KEY='COLE_SUA_CHAVE_AQUI'
   python citacoes.py
   ```

   **Não coloque a chave dentro do script ou em um arquivo versionado no Git.**

A execução atualiza `research/output.png` e **apenas os elementos identificados** em `publications.html` (total de citações na legenda, h-index e data).

Se a API falhar ou não retornar dados válidos, o script para com erro, sem publicar novas métricas.

## Atualização semanal automática no GitHub

1. Suba os arquivos novos para o repositório.
2. Em `github.com/gusmadeira/gusmadeira.github.io`, abra **Settings → Secrets and variables → Actions → New repository secret**.
3. Nome do segredo: `SERPAPI_API_KEY`. Valor: a sua chave privada da SerpApi.
4. Abra **Actions → Atualizar citacoes do Google Scholar → Run workflow** para testar.
5. **Antes do primeiro teste**, abra **Settings → Pages → Build and deployment → Source** e selecione **GitHub Actions** (em lugar de "Deploy from a branch"). O workflow publica o site diretamente, sem Jekyll. Isso é importante: commits do `GITHUB_TOKEN` sozinhos não acionam o build do Pages baseado em branch.
6. O workflow executa **todo domingo, às 08:17, horário do Rio de Janeiro**, embora o GitHub possa atrasar um disparo agendado.

O workflow também publica normalmente o site quando você faz `git push` para `main`, mas **não consulta a SerpApi nesses pushes** (só nos agendamentos ou ao usar **Run workflow**). Assim não consome créditos desnecessariamente.

O próprio workflow gera o gráfico, atualiza o HTML, registra esses dois arquivos no repositório e **faz o deploy do site na mesma execução**. Se `git push` falhar por falta de permissão, confira **Settings → Actions → General → Workflow permissions**. Se `deploy-pages` falhar, confira se **Source = GitHub Actions** e se Actions tem permissão para publicar em Pages.

## Observações

- O perfil Google Scholar pode conter preprints, teses e entradas duplicadas. Por isso, **24 peer-reviewed articles** e **14 first-author articles** permanecem manuais; a lista bibliográfica também não é tocada.
- Os números anuais no gráfico da prévia (2019–2026) vêm exclusivamente de `citacoes.py` fornecido, **não são verificados em tempo real**.
- Em 2026 e nos anos correntes, as citações do gráfico representam um **ano parcial**, mesmo depois de atualizar via API.
- Caso você altere os atributos `data-scholar-*` do HTML, o script interromperá a execução em vez de editar outro conteúdo por engano.
