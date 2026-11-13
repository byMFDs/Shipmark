# Política de privacidade

> **Rascunho**, última atualização em 14 de novembro de 2026. Este texto ainda não foi revisado por um advogado.
>
> Tradução por conveniência; a versão em inglês prevalece.

Esta página explica o que o {{ site_name }} guarda sobre você, por quê, por quanto tempo e o que você pode fazer a respeito. Ela descreve o que o site realmente faz.

## Quem é o responsável {#controller}

O {{ site_name }} é mantido por {{ legal_owner_name }}, que é responsável pelos seus dados (o “controlador”).
Dúvidas ou solicitações: [{{ contact_email }}](mailto:{{ contact_email }}).

## O que guardamos e por quê {#data}

**Quando você entra com o GitHub.** O GitHub nos envia:

- o id da sua conta, seu login, nome, bio, link do avatar e os outros campos públicos do seu perfil do GitHub;
- os endereços de e-mail da sua conta do GitHub.

Pedimos ao GitHub só duas permissões: `read:user` e `user:email`. Pela sua conta, nunca temos acesso aos seus repositórios, nem privados nem públicos. Não guardamos seu token de acesso do GitHub depois do login. Precisamos desses dados para criar sua conta e reconhecer você da próxima vez (execução do nosso acordo com você). Seu login do GitHub é atualizado a cada entrada, então seu perfil sempre leva à sua conta atual do GitHub.

**Seu perfil.** Nome de usuário, nome de exibição, resumo curto, “Sobre”, localização, um status (por exemplo, “Aberto a trabalho”), até 10 habilidades, até 6 links, até 3 projetos fixados e seu idioma. Tudo, exceto o nome de usuário, é opcional. O nome de exibição e o “Sobre” começam com seu nome e sua bio do GitHub; você pode mudá-los ou removê-los em Configurações. Também guardamos o endereço da sua imagem do GitHub, só para que “Usar minha imagem do GitHub” possa copiá-la; ela nunca é exibida. Seu nome de usuário, nome de exibição, resumo curto, “Sobre”, localização, status, habilidades, links, projetos fixados, login do GitHub e o mês em que você entrou são **públicos**.

**Foto de perfil e capa.** Você pode enviar uma foto e uma imagem de capa larga, ou copiar uma vez sua imagem do GitHub. Cada imagem é recodificada (a foto em 512×512, a capa em 1500×500), o que remove metadados ocultos como a localização GPS, recebe um nome de arquivo aleatório e é guardada no nosso próprio servidor: as páginas nunca carregam sua foto do GitHub. As duas são **públicas**. Quando você remove ou substitui uma delas, ou exclui sua conta, o arquivo é apagado; cópias ficam nos backups por até 14 dias. Sem foto, mostramos suas iniciais.

**Seu endereço de e-mail.** É guardado com a sua conta e visível apenas para a nossa equipe. Nunca é exibido no site. O site não envia e-mails para você (o único que envia é um aviso para a nossa equipe sobre uma mensagem ao suporte); usaríamos o endereço apenas para falar com você sobre a conta, uma denúncia ou uma mensagem ao suporte.

**Seus projetos.** Tudo o que você preenche: nome, slogan, descrição, links, tags, as ferramentas de IA que você diz ter usado (exibidas como declaradas pelo autor), capturas de tela e entradas do diário de desenvolvimento. Projetos publicados são públicos; rascunhos só são visíveis para você e para a nossa equipe. As capturas de tela são recodificadas no envio, o que remove metadados ocultos, como dados da câmera ou localização por GPS.

**Verificações de comprovação.** Para conceder selos, verificamos os fatos nós mesmos (nosso interesse legítimo em mostrar comprovações confiáveis):

- *Repo owner:* consultamos a API pública do GitHub sobre o repositório que você vincula e o verificamos de novo toda semana. A lista de outros colaboradores do GitHub é lida durante a verificação e não é guardada. Guardamos:
    - o id dele, o id da conta do dono, se ele é seu, a data de criação e o campo Website;
    - o primeiro commit do histórico (id e data);
    - o número dos seus commits, as datas do seu primeiro e último commit e o número de semanas com commits seus;
    - o estado de uma revisão manual, quando ela é necessária;
    - se o arquivo de verificação foi encontrado, quando você o usa em um repositório de organização.
- *Domain verified:* consultamos os registros DNS do domínio do seu projeto ou acessamos a página dele para encontrar seu token de verificação.
- *Steady:* acessamos o endereço do seu projeto a cada poucas horas e guardamos se ele respondeu e com que rapidez. Essas verificações ficam guardadas por **90 dias**.

Os resultados aparecem na página pública do seu projeto.

**Quem você segue e curtidas.** Guardamos quem você segue e quais projetos você curtiu. Os outros veem apenas os totais, não as listas.

**Denúncias e moderação.**

- Se você denunciar um projeto, um perfil ou uma entrada do diário de desenvolvimento, guardamos o motivo e os detalhes que você escrever.
- As denúncias são vistas pelos moderadores (pessoas com o badge de moderador) e pela equipe. Para decidir, eles também veem o conteúdo denunciado e o histórico da pessoa denunciada no {{ site_name }}: quando ela entrou, sanções anteriores, outras denúncias sobre ela e projetos removidos. As páginas de moderação não mostram endereços de e-mail.
- A pessoa denunciada nunca fica sabendo quem a denunciou.
- Quando os moderadores agem, guardamos a decisão e o motivo. Um projeto removido mantém o conteúdo e o motivo (só você, os moderadores e a equipe veem). Os campos do perfil limpos (foto e capa, título e “Sobre”, ou links) são apagados. Silenciamentos e banimentos são guardados com motivo, início e fim.
- Você vê o motivo em um aviso no site, que guardamos até você excluir sua conta. As decisões sobre você e esses avisos estão em “Baixar meus dados”.
- Para recorrer de uma decisão, escreva para [{{ contact_email }}](mailto:{{ contact_email }}).

**Comunidade.** Quando você publica na comunidade, guardamos:

- seus tópicos: seção, título, texto, datas e se um tópico foi editado, fixado, trancado ou removido;
- suas respostas: texto, a figurinha que você escolheu e a qual publicação elas respondem;
- as imagens que você anexa. Elas são recodificadas como as capturas de tela: metadados ocultos, como a localização GPS, são removidos, os nomes dos arquivos são aleatórios e guardamos uma cópia de até 1600 px e uma miniatura de 640 px no nosso próprio servidor.

As publicações, suas imagens, o número de votos e seu nome de usuário nelas são **públicos**. Também guardamos seus votos; ninguém vê quem votou em quê, nem no site nem na administração.

Quando você exclui uma publicação, o texto, a figurinha e as imagens são apagados na hora. O título de um tópico fica enquanto houver respostas de outras pessoas embaixo dele, mostrado como “[excluído]”. Quando os moderadores removem uma publicação, as imagens são apagadas na hora e o texto é guardado com o motivo, visível só para você, os moderadores e a equipe. Os moderadores veem as publicações denunciadas junto com o histórico do autor, como nas outras denúncias.

**Avisos de respostas.** Quando alguém responde ao seu tópico ou à sua resposta, guardamos um aviso para você (qual resposta, quando e quando você abriu a lista), além do horário do aviso não lido mais recente, para que o menu possa mostrar uma marca. Só você os vê. Eles são excluídos depois de **90 dias** ou junto com a sua conta. Nunca os enviamos por e-mail.

**Evasão de banimento.** Quando uma conta é banida, guardamos um hash de mão única, com sal, do id de usuário do GitHub (nunca o id em si), com o motivo e a data de fim. Ele serve apenas para reconhecer a mesma conta do GitHub se ela se cadastrar de novo durante o banimento. É apagado quando o banimento termina ou é revogado, também se a conta banida tiver sido excluída nesse meio-tempo.

**Aceite dos Termos.** Guardamos qual versão dos Termos você aceitou e quando.

**Registro de auditoria.** Mantemos um registro interno de mudanças de selos, ações de moderação e exclusões de contas, para que as decisões possam ser conferidas depois. Só a nossa equipe pode vê-lo.

**Endereços IP e registros.** O aplicativo não guarda seu endereço IP, e os registros dele não o contêm. De cada requisição de página, os registros anotam apenas o método, o endereço da página (sem o que vem depois de um `?`), o status da resposta, o tamanho e o tempo gasto, além dos erros. Não há dados do seu navegador. Os endereços de página incluem nomes de usuário (`/u/<username>/`), então uma linha de registro pode mostrar qual perfil foi aberto, mas não por quem.

**Registro de erros.** Quando algo falha, o aplicativo grava uma entrada curta em um arquivo de erros no nosso servidor. A entrada contém:

- a hora e um número de referência aleatório (o que aparece na página de erro);
- o método da requisição e o endereço da página sem o que vem depois de `?`, com os nomes de usuário trocados por `[user]`;
- o status da resposta e a parte do código que falhou;
- a mensagem técnica de erro, sem endereços de e-mail, endereços IP e qualquer coisa que pareça uma senha ou chave.

Páginas não encontradas vão para um arquivo separado, cada endereço no máximo uma vez por minuto. Esses arquivos nunca contêm seu endereço IP, dados do navegador, cookies, o que você digitou em um formulário, seu e-mail ou seu nome de usuário. Cada arquivo é limitado a 5 MB mais 5 cópias anteriores; ao atingir o limite, a mais antiga é apagada.

> **TODO antes do lançamento:** o servidor web na frente do aplicativo mantém seu próprio registro de acessos, que por padrão inclui endereços IP. O que ele registra e por quanto tempo guarda (e por quanto tempo os registros do aplicativo são guardados) ainda não foi decidido. É preciso preencher isso, ou desativar o registro de IP, antes de esta página se tornar pública.

**Proteção contra abusos.** Para limitar abusos, contamos algumas ações (por exemplo, curtidas por hora) no banco de dados do site. Cada contador é um número ligado à sua conta ou a um projeto, sem endereço IP, e vale por no máximo 24 horas. Depois disso deixa de ser usado, mas a linha pode ficar no banco até ser limpa. Uma exceção: quando você busca pessoas sem estar conectado, o contador fica ligado por 10 minutos a um hash unidirecional com sal do seu endereço IP (nunca ao próprio endereço). O que você busca nunca é guardado.

**Análise de uso e rastreamento.** Não há: nem análise de uso, nem publicidade, nem scripts de rastreamento. As fontes são servidas pelo nosso próprio servidor.

**Backups.** Todos os dias fazemos uma cópia do banco de dados e das imagens enviadas (capturas de tela, fotos de perfil e capas) e guardamos cada cópia por 14 dias. Se você excluir sua conta, seus dados ficam nesses backups até que o último que os contém seja substituído, no máximo 14 dias depois.

## Mensagens ao suporte {#support}

Quando você nos escreve pelo [formulário de suporte](/support/), guardamos o tema, o assunto, sua mensagem, o e-mail informado (ou o da sua conta), a conta com que você estava conectado, o número de referência de uma página de erro, se veio de uma, e até 3 anexos. As imagens são recodificadas como as outras (metadados ocultos, como a localização GPS, são removidos); arquivos de texto são guardados como texto. Os anexos ficam em uma pasta privada no nosso servidor, sem endereço público: só a equipe com acesso à caixa de suporte pode baixá-los. Usamos seu e-mail apenas para responder.

Não guardamos seu endereço IP nem dados do navegador com a mensagem. Para barrar spam, uma impressão digital unidirecional e com sal do seu endereço IP fica no cache do servidor por no máximo 24 horas, nunca no banco de dados nem nos registros.

Quando uma mensagem chega, nosso servidor envia para a caixa da equipe um aviso curto em texto simples com sua mensagem e seu e-mail, pelo nosso provedor de e-mail (veja “Quem mais recebe dados”). A equipe pode adicionar notas internas e definir um status (nova, lida, respondida, encerrada). Lemos todas as mensagens, mas não podemos prometer responder a todas. Mensagens encerradas são excluídas 12 meses depois do envio; as demais ficam até serem encerradas. “Baixar meus dados” inclui as mensagens enviadas com a sua conta, e excluir a conta as apaga, inclusive as enviadas sem login a partir do e-mail da sua conta.

## Por quanto tempo guardamos {#retention}

- Sua conta, perfil, projetos, quem você segue e curtidas: até você excluí-los ou excluir a conta.
- Mensagens ao suporte e anexos: encerradas, 12 meses após o envio; as demais, até serem encerradas; junto com a sua conta.
- Tópicos, respostas e imagens da comunidade: até você excluí-los ou excluir sua conta (o que fica está descrito acima, em “Comunidade”). Votos: até você retirá-los ou excluir sua conta.
- Avisos de respostas: 90 dias.
- Foto de perfil e capa: até você removê-las ou substituí-las, ou excluir sua conta.
- Verificações de disponibilidade: 90 dias.
- Decisões de moderação sobre você (silenciamentos, banimentos, projetos removidos) e avisos: enquanto sua conta existir; são apagados com ela. Denúncias sobre você ficam sem vínculo com a conta, só com o nome mostrado na época.
- Hash do id do GitHub de uma conta banida: só até o banimento terminar ou ser revogado.
- Sessões de login: 2 semanas, ou até você sair da conta.
- Denúncias que você fez: permanecem depois de tratadas. Se você excluir sua conta, ficam sem o seu nome.
- Registro de auditoria: é mantido. As entradas sobre uma conta excluída não contêm o nome de usuário nem o e-mail.
- Contadores de proteção contra abusos: no máximo 24 horas.
- Backups: 14 dias. Uma conta excluída some deles em até 14 dias.
- Arquivos do registro de erros: até encherem (5 MB mais 5 cópias anteriores de 5 MB), depois as entradas mais antigas são apagadas.
- Registros do servidor web e do aplicativo: **TODO**, ainda não decidido.

## Quem mais recebe dados {#recipients}

- **GitHub, Inc.** Você entra em github.com, e o nosso servidor lê seu perfil e dados públicos de repositórios pela API do GitHub. A declaração de privacidade do próprio GitHub vale para o seu uso do GitHub.
- **Nosso provedor de e-mail** (por exemplo, o Google, se a caixa da equipe for uma conta do Gmail) entrega na caixa da equipe o aviso de cada mensagem ao suporte, com o texto e o seu e-mail.
- **Os servidores do seu projeto.** Nas verificações de Domain verified e Steady, o nosso servidor acessa o DNS do seu domínio e o endereço do seu projeto. Eles veem o nosso servidor, não você.
- **Nosso provedor de hospedagem**, que mantém o servidor e o banco de dados para nós.

Não vendemos seus dados nem os compartilhamos para publicidade.

## Seus direitos {#rights}

- **Ver e baixar seus dados:** em Configurações → “Baixar meus dados” você recebe um arquivo JSON com seu perfil (com seus links, habilidades, projetos fixados e os endereços da sua foto e da sua capa), dados do GitHub, projetos, diário de desenvolvimento, curtidas, quem você segue, as denúncias que fez e as decisões de moderação e avisos sobre você.
- **Corrigi-los:** edite seu perfil em Configurações e seus projetos nas páginas deles.
- **Excluí-los:** Configurações → “Excluir conta”. Isso remove na hora seu perfil, sua foto e sua capa e todos os seus projetos, curtidas e quem você segue, e não pode ser desfeito. Seu nome de usuário fica livre.
- **Comunidade:** “Baixar meus dados” também inclui seus tópicos, respostas, os endereços das suas imagens, seus votos e seus avisos de respostas. Excluir sua conta apaga suas imagens da comunidade, seus votos, seus avisos e seus tópicos sem respostas de outras pessoas; as demais publicações ficam sem seu nome, sua foto e seu link. As imagens da comunidade ficam nos backups diários, como os outros envios (14 dias).
- **Se opor ou reclamar:** escreva para [{{ contact_email }}](mailto:{{ contact_email }}). Se você mora na UE, no Reino Unido ou na Ucrânia, também pode reclamar à sua autoridade de proteção de dados.

## Cookies {#cookies}

Usamos apenas os cookies de que o site precisa para funcionar. Veja a [política de cookies](/legal/cookies/).

## Alterações {#changes}

Se esta política mudar, atualizamos a data no topo. Se a mudança for importante, pediremos que você aceite os Termos atualizados na sua próxima visita.
