# Análise de Riscos — To-Do List API

**Data da análise:** 2026-07-16
**Escopo:** MVP de API REST para gerenciamento de tarefas (FastAPI + SQLite)

---

## 1. Análise estruturada dos riscos

### Risco 1: Caminho do banco de dados hardcoded

- **Descrição:** O caminho do banco depende do diretório de execução e pode produzir comportamento inconsistente entre ambiente local, testes e futuras execuções automatizadas.
- **Possíveis impactos no projeto:** criação de banco em local inesperado, falhas de conexão difíceis de diagnosticar, divergência entre dados esperados e dados usados durante testes, e retrabalho para ajustar a configuração de ambiente.
- **Fatores que influenciam a ocorrência:** execução fora da raiz do projeto, uso de scripts ou testes com diretório corrente diferente, e eventual adoção de containerização ou CI/CD.
- **Probabilidade (qualitativa):** Média
- **Impacto (qualitativo):** Médio
- **Justificativa da classificação:** o risco já existe no código atual, mas sua materialização depende do modo de execução. O impacto tende a ser relevante para a operação, embora normalmente seja detectável com testes de ambiente.

### Risco 2: Ausência de ferramenta de migração de schema

- **Descrição:** O schema é criado de forma inicial, porém sem mecanismo de evolução versionada; alterações no modelo podem não ser refletidas automaticamente no banco existente.
- **Possíveis impactos no projeto:** necessidade de intervenção manual, inconsistência entre código e banco, aumento do esforço de manutenção e maior chance de falhas em ambientes com dados já existentes.
- **Fatores que influenciam a ocorrência:** mudanças no modelo `Task`, persistência de dados entre versões, necessidade de compatibilidade retroativa e ausência de processo formal de migração.
- **Probabilidade (qualitativa):** Média
- **Impacto (qualitativo):** Alto
- **Justificativa da classificação:** a evolução do escopo foi antecipada no contexto do projeto, então a ocorrência é plausível; o impacto é alto porque o problema afeta integridade e continuidade do banco de dados.

### Risco 3: Campo `status` persistido como String sem restrição no banco

- **Descrição:** A aplicação valida o campo na camada de entrada, mas o banco não impede valores fora do conjunto esperado.
- **Possíveis impactos no projeto:** corrupção lógica dos dados, retorno de estados inválidos pela API, necessidade de saneamento manual e risco de falhas em integrações que assumem valores restritos.
- **Fatores que influenciam a ocorrência:** manipulação direta do banco, scripts de carga ou testes fora do fluxo da API, e ausência de constraint no nível do banco.
- **Probabilidade (qualitativa):** Média
- **Impacto (qualitativo):** Médio
- **Justificativa da classificação:** a validação pela API reduz a exposição no uso normal, mas o modelo atual ainda permite inconsistências quando há acesso direto ao banco; o impacto costuma se concentrar em qualidade e confiabilidade dos dados.

### Risco 4: Ausência de paginação expõe risco de degradação de desempenho

- **Descrição:** A listagem retorna todos os registros sem limite, o que é aceitável no MVP, mas não escala bem com o aumento de volume.
- **Possíveis impactos no projeto:** respostas maiores, maior consumo de memória, aumento de latência, pior experiência de uso e possíveis gargalos em ambientes de teste com massa de dados.
- **Fatores que influenciam a ocorrência:** crescimento da base de tarefas, testes com muitos registros, execução prolongada do sistema e ausência de filtros ou limites de retorno.
- **Probabilidade (qualitativa):** Baixa
- **Impacto (qualitativo):** Médio
- **Justificativa da classificação:** no escopo atual o volume tende a ser pequeno, então a ocorrência não é imediata; quando ocorrer, o impacto é perceptível em desempenho e consumo de recursos, embora não comprometa diretamente a correção funcional.

### Risco 5: Ausência de arquivo de lock de dependências

- **Descrição:** As dependências diretas estão pinadas, mas a resolução de dependências transitivas pode variar entre instalações.
- **Possíveis impactos no projeto:** diferenças de comportamento entre ambientes, dificuldade para reproduzir bugs, variação de resultados em testes e maior esforço de suporte ao onboarding de novos membros.
- **Fatores que influenciam a ocorrência:** instalações em máquinas diferentes, ausência de ambiente virtual padronizado, atualizações indiretas de pacotes e eventual uso em pipelines futuros.
- **Probabilidade (qualitativa):** Alta
- **Impacto (qualitativo):** Médio
- **Justificativa da classificação:** a falta de lock afeta qualquer instalação nova, portanto a probabilidade é elevada; o impacto costuma se manifestar como inconsistência e retrabalho, mais do que como falha catastrófica.

### Risco 6: Evolução de requisitos pode exigir refatoração estrutural significativa

- **Descrição:** A arquitetura foi pensada para o MVP atual e pode não absorver bem novos requisitos como autenticação, multi-tenancy ou outro banco sem mudanças estruturais.
- **Possíveis impactos no projeto:** aumento forte de esforço de desenvolvimento, atraso no cronograma, refatoração com risco de regressões e maior necessidade de coordenação entre membros da equipe.
- **Fatores que influenciam a ocorrência:** mudança de escopo de negócio, entrada de requisitos não previstos, necessidade de integração com serviços externos e pressão por compatibilidade com a base atual.
- **Probabilidade (qualitativa):** Média
- **Impacto (qualitativo):** Alto
- **Justificativa da classificação:** o risco depende de uma mudança de escopo, portanto não é imediato, mas é plausível no ciclo de vida do produto; se ocorrer, tende a afetar diretamente prazo, arquitetura e estabilidade.

### Risco 7: Coordenação de padrões de código em equipe distribuída sem configuração de linting/formatação

- **Descrição:** Sem ferramentas automáticas de estilo e análise, contribuições podem seguir padrões diferentes e aumentar o custo de revisão.
- **Possíveis impactos no projeto:** retrabalho em pull requests, divergência de estilo, aumento do tempo de revisão, maior chance de inconsistências e, em casos pontuais, introdução de bugs simples.
- **Fatores que influenciam a ocorrência:** trabalho distribuído, ausência de padronização automatizada, chegada de novos desenvolvedores e diferentes hábitos de edição local.
- **Probabilidade (qualitativa):** Alta
- **Impacto (qualitativo):** Médio
- **Justificativa da classificação:** em equipe distribuída, a variabilidade de estilo é muito provável sem automação; o impacto é relevante para coordenação e qualidade, embora normalmente não impeça a entrega funcional.

### Risco 8: Requisição `PATCH` sem campos preenchidos é aceita silenciosamente

- **Descrição:** O endpoint aceita atualização vazia e retorna sucesso mesmo sem alteração efetiva.
- **Possíveis impactos no projeto:** mascaramento de falhas de integração, dificuldade para diagnosticar clientes com payloads inválidos, falsas confirmações de atualização e aumento do custo de suporte.
- **Fatores que influenciam a ocorrência:** clientes que montam payloads dinamicamente, ausência de validação adicional no serviço e consumo da API por scripts ou frontends em evolução.
- **Probabilidade (qualitativa):** Média
- **Impacto (qualitativo):** Baixo
- **Justificativa da classificação:** o cenário depende de erro do cliente ou integração, então não é inevitável; o impacto tende a ser mais de depuração e qualidade de integração do que de dano funcional direto.

## 2. Matriz Qualitativa de Riscos

| Probabilidade\Impacto | Baixo | Médio | Alto |
| ----------------------- | ----- | ----- | ---- |
| **Alta** |  | Risco 5, Risco 7 |  |
| **Média** | Risco 8 | Risco 1, Risco 3, Risco 4 | Risco 2, Risco 6 |
| **Baixa** |  |  |  |

Observação: a classificação é qualitativa e reflete o contexto atual do MVP; alguns riscos podem migrar de célula caso o escopo, o volume de dados ou o modelo de operação evoluam.