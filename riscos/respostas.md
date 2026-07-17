# Respostas aos Riscos — To-Do List API

**Data da análise:** 2026-07-16
**Escopo:** MVP de API REST para gerenciamento de tarefas (FastAPI + SQLite)
**Referências:** `identificação.md`, `analise.md`

---

## 1. Estratégias Possíveis por Risco

---

### Risco 1: Caminho do banco de dados hardcoded

- **Descrição:** O `DATABASE_URL` está fixo como `"sqlite:///./app/db/todolist.db"` no código-fonte, fazendo com que o comportamento dependa do diretório de trabalho no momento da execução.

- **Estratégias de resposta possíveis:**

  - **i. Evitar:** Remover o caminho hardcoded por completo, substituindo-o por uma variável de ambiente obrigatória (`DATABASE_URL`) sem valor padrão. Dessa forma, a aplicação não inicializa sem configuração explícita, eliminando a ambiguidade de diretório. Implica que todo ambiente — local, teste e futuro CI/CD — deve declarar a variável.

  - **ii. Mitigar:** Carregar o valor a partir de uma variável de ambiente com fallback para o caminho atual (usando `os.getenv` ou `python-dotenv`). Isso reduz a probabilidade de inconsistência sem eliminar o risco completamente, pois o fallback ainda depende do diretório de execução.

  - **iii. Transferir:** Delegar a responsabilidade de configuração do banco a um arquivo `.env` ou a um sistema de gerenciamento de configuração externo (ex.: AWS SSM Parameter Store no futuro), tornando o ambiente, e não o código, o responsável pela corretude do caminho.

  - **iv. Aceitar:** Manter o hardcode e documentar explicitamente que a aplicação deve ser sempre iniciada a partir da raiz do projeto. Estratégia viável apenas enquanto a equipe for pequena, o processo de execução for manual e não houver containerização ou CI/CD.

---

### Risco 2: Ausência de ferramenta de migração de schema

- **Descrição:** O schema é criado via `Base.metadata.create_all()`, sem controle de versão de migrações. Alterações no modelo ORM não são propagadas automaticamente para bancos já existentes.

- **Estratégias de resposta possíveis:**

  - **i. Evitar:** Integrar Alembic ao projeto desde agora, antes que qualquer dado de produção exista. Criar a migration inicial a partir do estado atual do modelo evita a lacuna entre código e banco desde o início do ciclo de vida dos dados.

  - **ii. Mitigar:** Adotar uma política de equipe que exija scripts SQL de migração manual toda vez que o modelo for alterado, com registro versionado no repositório (ex.: pasta `migrations/` com arquivos `v001_add_campo.sql`). Reduz o impacto, mas aumenta o esforço operacional.

  - **iii. Transferir:** Não aplicável de forma direta para este risco técnico; a responsabilidade é intrínseca ao desenvolvimento e não pode ser delegada externamente de maneira significativa dentro do contexto do MVP.

  - **iv. Aceitar:** Aceitar temporariamente a ausência de migrations enquanto o modelo estiver estável e não houver dados persistentes que precisem sobreviver entre versões. Essa aceitação deve ser revisada imediatamente quando o modelo `Task` for alterado pela primeira vez.

---

### Risco 3: Campo `status` persistido como String sem restrição no banco

- **Descrição:** A validação dos valores `"pending"` / `"completed"` ocorre apenas na camada Pydantic. O banco não impede a inserção de valores fora desse conjunto por acesso direto.

- **Estratégias de resposta possíveis:**

  - **i. Evitar:** Declarar o campo `status` como um tipo `Enum` nativo do SQLAlchemy no modelo ORM. Isso transfere a restrição para o DDL do banco, impedindo valores inválidos independentemente do caminho de acesso utilizado.

  - **ii. Mitigar:** Adicionar uma `CheckConstraint` ao modelo ORM (`CHECK (status IN ('pending', 'completed'))`), que é gerada no DDL sem exigir migração complexa. Mantém a validação dupla (Pydantic + banco) sem alterar a estrutura do código de forma significativa.

  - **iii. Transferir:** Estabelecer um processo de revisão obrigatória antes de qualquer acesso direto ao banco, delegando a responsabilidade de validação ao processo humano (ex.: checklist de QA para scripts de seed). Reduz a exposição, mas não elimina o risco técnico.

  - **iv. Aceitar:** Aceitar a validação apenas na camada Pydantic enquanto o único canal de acesso ao banco for a própria API. Estratégia razoável para o MVP, desde que sejam documentadas as restrições de acesso direto ao arquivo `.db`.

---

### Risco 4: Ausência de paginação expõe risco de degradação de desempenho

- **Descrição:** O endpoint `GET /tasks` retorna todos os registros sem limite ou offset, o que não escala com o crescimento do volume de dados.

- **Estratégias de resposta possíveis:**

  - **i. Evitar:** Implementar paginação desde o MVP, adicionando parâmetros `skip` e `limit` ao endpoint e ao repositório. Elimina o risco antes de qualquer impacto, com custo de implementação baixo neste momento.

  - **ii. Mitigar:** Inserir um limite máximo implícito no repositório (ex.: `LIMIT 500`) sem expor paginação na API. Reduz o impacto de um crescimento inesperado de dados sem alterar a interface pública do endpoint.

  - **iii. Transferir:** Não aplicável diretamente; o risco de desempenho não pode ser transferido a terceiros no contexto de uma API REST simples sem infraestrutura externa de cache ou CDN.

  - **iv. Aceitar:** Aceitar a ausência de paginação dado que o volume de dados no MVP é reconhecidamente pequeno e controlado. Registrar a dívida técnica explicitamente (ex.: no backlog ou no `README`) para endereçamento antes de qualquer crescimento de escala.

---

### Risco 5: Ausência de arquivo de lock de dependências

- **Descrição:** As dependências diretas estão pinadas no `requirements.txt`, mas as dependências transitivas podem ser resolvidas de forma diferente em cada instalação.

- **Estratégias de resposta possíveis:**

  - **i. Evitar:** Migrar o gerenciamento de dependências para uma ferramenta que gere arquivo de lock nativo — como `uv` (com `uv.lock`), `Poetry` (com `poetry.lock`) ou `pip-compile` (com `requirements.lock`). O lock file elimina a variabilidade de dependências transitivas entre ambientes.

  - **ii. Mitigar:** Gerar um `requirements.txt` completo via `pip freeze > requirements-lock.txt` a partir de um ambiente de referência e utilizar esse arquivo nas instalações. Reduz a variabilidade sem exigir mudança de ferramenta, mas o arquivo precisa ser mantido manualmente a cada atualização.

  - **iii. Transferir:** Delegar a garantia de reprodutibilidade a uma imagem Docker que encapsula o ambiente completo. A responsabilidade de consistência migra da resolução de dependências para o processo de build da imagem.

  - **iv. Aceitar:** Aceitar a variabilidade transitiva enquanto a equipe for pequena, os ambientes forem similares e não houver histórico de bugs causados por divergências de dependências. Estratégia de menor custo imediato, com risco crescente conforme a equipe aumenta.

---

### Risco 6: Evolução de requisitos pode exigir refatoração estrutural significativa

- **Descrição:** A arquitetura atual não possui pontos de extensão para autenticação, multi-tenancy ou troca de banco de dados — todos explicitamente fora do escopo MVP.

- **Estratégias de resposta possíveis:**

  - **i. Evitar:** Incorporar ao design atual abstrações mínimas que facilitem extensão futura — como injeção de dependência para o repositório e separação clara das camadas — mesmo sem implementar os recursos. Isso reduz o custo de refatoração futura sem adicionar funcionalidade desnecessária agora.

  - **ii. Mitigar:** Documentar explicitamente as decisões arquiteturais e seus limites (Architecture Decision Records — ADRs), de modo que qualquer expansão de escopo inicie com diagnóstico claro dos pontos de ruptura. Reduz o risco de regressões silenciosas ao facilitar o entendimento do impacto de mudanças.

  - **iii. Transferir:** Envolver os stakeholders de negócio em decisões de roadmap que possam ampliar o escopo, tornando a discussão de custo de refatoração parte do processo de aprovação de novos requisitos. Transfere parte da responsabilidade de gestão do risco ao processo de governança.

  - **iv. Aceitar:** Aceitar os limites arquiteturais como condição do MVP, com comprometimento explícito de revisão arquitetural antes de qualquer feature que extrapole o escopo atual. Estratégia adequada quando o horizonte de evolução é incerto e o custo de over-engineering supera o benefício.

---

### Risco 7: Ausência de configuração de linting/formatação para equipe distribuída

- **Descrição:** Sem ferramentas automatizadas de estilo e análise estática, contribuições de diferentes membros da equipe podem seguir padrões divergentes.

- **Estratégias de resposta possíveis:**

  - **i. Evitar:** Adicionar configuração de linting (`ruff`) e formatação (`black` ou o próprio `ruff format`) ao projeto, com execução obrigatória pré-commit via `pre-commit`. Elimina a variabilidade de estilo antes que ela chegue ao repositório.

  - **ii. Mitigar:** Criar um guia de contribuição (`CONTRIBUTING.md`) com as convenções de estilo adotadas e um checklist de revisão de PR. Reduz a divergência sem automação, mas depende de adesão voluntária dos membros da equipe.

  - **iii. Transferir:** Configurar o linting como etapa obrigatória em um pipeline de CI/CD futuro, delegando a verificação de conformidade ao processo automatizado de integração. A responsabilidade de conformidade migra do revisor humano para o sistema.

  - **iv. Aceitar:** Aceitar a ausência de automação enquanto a equipe for pequena e os padrões forem informalmente alinhados. Estratégia de custo zero imediato, porém com tendência de deterioração proporcional ao crescimento da equipe.

---

### Risco 8: Requisição PATCH sem campos preenchidos é aceita silenciosamente

- **Descrição:** Um `PATCH` com body `{}` é válido, não retorna erro e resulta em operação de banco sem efeito, retornando `200 OK` com dados inalterados.

- **Estratégias de resposta possíveis:**

  - **i. Evitar:** Adicionar validação no nível do schema Pydantic ou da camada de serviço que rejeite payloads sem nenhum campo preenchido, retornando `422 Unprocessable Entity`. Elimina o comportamento silencioso na origem.

  - **ii. Mitigar:** Retornar `200 OK` com um campo adicional na resposta que indique explicitamente se algum campo foi de fato alterado (ex.: `"updated": false`). Mantém a permissividade, mas torna o comportamento transparente para o cliente.

  - **iii. Transferir:** Documentar o comportamento atual na especificação OpenAPI (docstring do endpoint), transferindo a responsabilidade de interpretação correta ao cliente da API. Não elimina nem reduz o risco técnico, mas reduz a ambiguidade para integradores.

  - **iv. Aceitar:** Aceitar o comportamento atual dado que o impacto é classificado como baixo e a correção pode ser postergada. O `200 OK` sem efeito não corrompe dados nem gera falha funcional; o custo de depuração eventual é considerado tolerável no contexto do MVP.

---

## 2. Considerações sobre Aplicação das Estratégias

### Quando cada tipo de estratégia tende a ser mais adequada

| Estratégia | Situações mais adequadas |
|------------|--------------------------|
| **Evitar** | O custo de implementação da prevenção é baixo; o risco tem alta probabilidade ou impacto alto; a janela de oportunidade para agir sem retrabalho ainda está aberta (ex.: antes de dados existirem em produção). |
| **Mitigar** | Evitar o risco é impraticável ou custoso demais; é possível reduzir probabilidade ou impacto com mudanças pontuais; o risco é aceitável em nível reduzido. |
| **Transferir** | Existe um ator externo (ferramenta, processo, contrato) que pode absorver o risco de forma mais eficiente; o risco envolve conformidade, responsabilidade ou variabilidade de ambiente. |
| **Aceitar** | O custo de tratamento supera o impacto esperado; o risco é de baixa probabilidade ou impacto baixo; o risco está fora do controle imediato da equipe; a aceitação é temporária e documentada. |

### Limitações e trade-offs por abordagem

- **Evitar** pode gerar over-engineering se aplicado a riscos de baixo impacto, adicionando complexidade desnecessária ao MVP.
- **Mitigar** reduz, mas não elimina o risco; exige monitoramento contínuo para verificar se as medidas permanecem eficazes conforme o contexto evolui.
- **Transferir** desloca a responsabilidade, mas não elimina a exposição ao risco; a efetividade depende da confiabilidade do ator receptor (ferramenta, processo, contrato).
- **Aceitar** é a estratégia de menor custo imediato, porém carrega o risco de negligência se não acompanhada de revisão periódica e registro formal da decisão.

---

## 3. Observações Gerais

### Dependência de contexto adicional para tomada de decisão

- **Horizonte de evolução do produto:** As estratégias para os Riscos 2, 4 e 6 dependem fortemente de quanto o escopo tende a crescer além do MVP. Sem clareza sobre o roadmap, a recomendação entre evitar e aceitar fica tecnicamente indeterminada.
- **Tamanho e maturidade da equipe:** As estratégias para os Riscos 5 e 7 ganham ou perdem urgência dependendo de quantos membros novos serão integrados e da senioridade média da equipe.
- **Prazo e capacidade atual:** A viabilidade das estratégias de evitar (ex.: integrar Alembic, configurar linting, implementar paginação) depende do bandwidth disponível no sprint atual.
- **Dados existentes em produção:** O Risco 2 muda de categoria de urgência radicalmente dependendo de se já existem dados que precisam ser preservados entre versões do modelo.

### Pontos que exigem validação com stakeholders

- **Risco 6:** A decisão de investir em abstrações arquiteturais antecipadas deve ser alinhada com os patrocinadores do projeto, pois afeta diretamente o cronograma de entrega do MVP.
- **Risco 4:** O limite aceitável de volume de tarefas antes que paginação se torne necessária deve ser discutido com os usuários ou product owners que definem os critérios de aceitação.
- **Risco 8:** O comportamento esperado do endpoint `PATCH` (permissivo vs. restritivo) deve ser validado com os integradores da API — clientes que já consomem o endpoint podem depender do comportamento atual.
- **Riscos 1 e 5:** A adoção de variáveis de ambiente e lock files deve ser validada com todos os membros da equipe para garantir que o processo de setup local seja atualizado de forma coordenada.

---

*Esta análise é de caráter exploratório e qualitativo. As estratégias apresentadas não constituem uma recomendação definitiva; a escolha final deve considerar o contexto operacional, os recursos disponíveis e as prioridades acordadas entre a equipe e os stakeholders.*
