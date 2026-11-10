# Política de privacidade

> **Rascunho**, última atualização em 10 de novembro de 2026. Este texto ainda não foi revisado por um advogado.
>
> Tradução por conveniência; a versão em inglês prevalece.

Esta página explica o que o {{ site_name }} guarda sobre você, por quê, por quanto tempo e o que você pode fazer a respeito. Ela descreve o que o site realmente faz.

## Quem é o responsável {#controller}

O {{ site_name }} é mantido por {{ legal_owner_name }}, que é responsável pelos seus dados (o “controlador”).
Dúvidas ou solicitações: [{{ contact_email }}](mailto:{{ contact_email }}).

## O que guardamos e por quê {#data}

**Quando você entra com o GitHub.** Recebemos do GitHub o id da sua conta, seu login, nome, bio, o link do seu avatar e os demais campos públicos do seu perfil do GitHub, além dos endereços de e-mail da sua conta do GitHub. Pedimos ao GitHub apenas `read:user` e `user:email`: nunca obtemos acesso aos seus repositórios, privados ou públicos, por meio da sua conta. Não guardamos seu token de acesso do GitHub depois do login. Precisamos disso para criar sua conta e reconhecer você na próxima vez (execução do nosso acordo com você).

**Seu perfil.** Nome de usuário, nome de exibição, bio, site e idioma. O nome e a bio começam com os seus valores do GitHub; você pode alterá-los em Configurações. Seu nome de usuário, nome de exibição, bio, site, login do GitHub e o mês em que você entrou são **públicos**.

**Seu endereço de e-mail.** É guardado com a sua conta e visível apenas para a nossa equipe. Nunca é exibido no site. O site não envia e-mails; usaríamos o endereço apenas para falar com você sobre a conta ou uma denúncia.

**Seus projetos.** Tudo o que você preenche: nome, slogan, descrição, links, tags, as ferramentas de IA que você diz ter usado (exibidas como declaradas pelo autor), capturas de tela e entradas do diário de desenvolvimento. Projetos publicados são públicos; rascunhos só são visíveis para você e para a nossa equipe. As capturas de tela são recodificadas no envio, o que remove metadados ocultos, como dados da câmera ou localização por GPS.

**Verificações de comprovação.** Para conceder selos, verificamos os fatos nós mesmos (nosso interesse legítimo em mostrar comprovações confiáveis):

- *Authored:* consultamos a API pública do GitHub sobre o repositório que você vincula e guardamos se ele é seu, sua contagem de commits e as datas do primeiro e do último commit. A lista dos demais colaboradores do GitHub é lida durante a verificação e não é guardada.
- *Live:* consultamos os registros DNS do domínio do seu projeto ou acessamos a página dele para encontrar seu token de verificação.
- *Steady:* acessamos o endereço do seu projeto a cada poucas horas e guardamos se ele respondeu e com que rapidez. Essas verificações ficam guardadas por **90 dias**.

Os resultados aparecem na página pública do seu projeto.

**Quem você segue e curtidas.** Guardamos quem você segue e quais projetos você curtiu. Os outros veem apenas os totais, não as listas.

**Denúncias.** Se você denunciar um projeto ou um perfil, guardamos o motivo e os detalhes que você escrever. Só a nossa equipe vê as denúncias. A pessoa denunciada não é informada de quem a denunciou.

**Aceite dos Termos.** Guardamos qual versão dos Termos você aceitou e quando.

**Registro de auditoria.** Mantemos um registro interno de mudanças de selos, ações de moderação e exclusões de contas, para que as decisões possam ser conferidas depois. Só a nossa equipe pode vê-lo.

**O que não guardamos.** O site não registra seu endereço IP. Para limitar abusos, contamos ações por conta (por exemplo, curtidas por hora) em memória temporária por no máximo uma hora. Não há análise de uso, publicidade nem scripts de rastreamento. As fontes são servidas pelo nosso próprio servidor.

## Por quanto tempo guardamos {#retention}

- Sua conta, perfil, projetos, quem você segue e curtidas: até você excluí-los ou excluir a conta.
- Verificações de disponibilidade: 90 dias.
- Sessões de login: 2 semanas, ou até você sair da conta.
- Denúncias que você fez: permanecem depois de tratadas. Se você excluir sua conta, ficam sem o seu nome.
- Registro de auditoria: é mantido. As entradas sobre uma conta excluída não contêm o nome de usuário nem o e-mail.

## Quem mais recebe dados {#recipients}

- **GitHub, Inc.** Você entra em github.com, e o nosso servidor lê seu perfil e dados públicos de repositórios pela API do GitHub. A declaração de privacidade do próprio GitHub vale para o seu uso do GitHub.
- **Os servidores do seu projeto.** Nas verificações de Live e Steady, o nosso servidor acessa o DNS do seu domínio e o endereço do seu projeto. Eles veem o nosso servidor, não você.
- **Nosso provedor de hospedagem**, que mantém o servidor e o banco de dados para nós.

Não vendemos seus dados nem os compartilhamos para publicidade.

## Seus direitos {#rights}

- **Ver e baixar seus dados:** em Configurações → “Baixar meus dados” você recebe um arquivo JSON com seu perfil, dados do GitHub, projetos, diário de desenvolvimento, curtidas, quem você segue e as denúncias que fez.
- **Corrigi-los:** edite seu perfil em Configurações e seus projetos nas páginas deles.
- **Excluí-los:** Configurações → “Excluir conta”. Isso remove na hora seu perfil e todos os seus projetos, curtidas e quem você segue, e não pode ser desfeito. Seu nome de usuário fica livre.
- **Se opor ou reclamar:** escreva para [{{ contact_email }}](mailto:{{ contact_email }}). Se você mora na UE, no Reino Unido ou na Ucrânia, também pode reclamar à sua autoridade de proteção de dados.

## Cookies {#cookies}

Usamos apenas os cookies de que o site precisa para funcionar. Veja a [política de cookies](/legal/cookies/).

## Alterações {#changes}

Se esta política mudar, atualizamos a data no topo. Se a mudança for importante, pediremos que você aceite os Termos atualizados na sua próxima visita.
