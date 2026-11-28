# Produção — 3. Rodar como serviço na porta 8093

Pré-requisito: o [passo 2](02-sistema-e-dados.md) concluído, com o sistema instalado e o backup restaurado.

O servidor só publica o site em `http://<ip-do-servidor>:8093`. O HTTPS e o domínio (`xxx.hybrazil.com`) ficam no **HAProxy do pfSense**, que encaminha para essa porta.

## 1. Publicar

```bash
cd /opt/hybrazil-cases
sudo git pull
sudo bash scripts/producao/publicar.sh
```

O script faz o seguinte:

| Etapa | O que acontece |
|---|---|
| `COOKIE_SECURE=true` | Liga no `backend/.env`. O cookie de login só trafega por HTTPS. |
| Serviço `hybrazil-cases` | Roda o site com o usuário `hybrazil` na porta 8093. Sobe sozinho com o servidor e reinicia sozinho se cair. Tem proteções do systemd: o site só consegue gravar em `/var/lib/hybrazil-cases`. |
| Firewall | Libera a porta 8093. |

O resultado esperado no final é `Site publicado em http://<ip>:8093`.

Opções:

- **`--porta N`:** usa outra porta.
- **`--proxy <ip-do-pfsense>`:** só o pfSense acessa a porta. Além disso, o site passa a registrar o IP real de quem entra, em vez do IP do pfSense. Para isso, ligue o `forwardfor` no HAProxy.

O script pode ser rodado de novo sem problema.

## 2. No pfSense

Aponte o backend do HAProxy para `<ip-do-servidor>:8093`, sem SSL. A verificação de saúde pode usar `GET /api/saude`.

Como os anexos vão até 1 GB, vale deixar o **server timeout** em alguns minutos, por exemplo 300 s.

> Com `COOKIE_SECURE=true`, o login só funciona pelo endereço `https://` do domínio. Pelo `http://<ip>:8093` direto, a página abre, mas o login volta para a tela inicial.

## 3. Atualizar o sistema

Quando houver uma versão nova no GitHub:

```bash
cd /opt/hybrazil-cases
sudo bash scripts/producao/atualizar.sh
```

O script baixa o código, reinstala as dependências, recompila a interface e reinicia o serviço. As atualizações de banco são aplicadas sozinhas na subida. Se o site não voltar, ele mostra o log e o comando para voltar à versão anterior.

> Faça um backup antes de atualizações grandes. As atualizações de banco não são desfeitas ao voltar o código.

## Comandos úteis

```bash
systemctl status hybrazil-cases            # o site está rodando?
sudo journalctl -u hybrazil-cases -f       # log do site, ao vivo (Ctrl+C sai)
sudo systemctl restart hybrazil-cases      # reiniciar o site
```

## Próximo passo

4. Configurar o backup semanal para o SharePoint, mantendo os 2 últimos.
