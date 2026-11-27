# Ora API — referência completa

Gerado automaticamente a partir de [`swagger.json`](swagger.json): a especificação oficial publicada em `https://api.ora.pm/swagger.json`, **cópia do Internet Archive de 04/02/2026** (https://web.archive.org/web/20260204233546/https://api.ora.pm/swagger.json). Os textos das descrições são os originais, em inglês.

- **Autenticação:** OAuth2 *authorization code* — autorizar em `https://app.ora.pm/authorize`, token em `https://api.ora.pm/oauth/token`; enviar `Authorization: Bearer <access_token>`.
- **Endereço base:** `https://api.ora.pm` (caminhos abaixo relativos a ele).
- **Paginação:** onde existem, `offset` (itens já exibidos) e `limit` (itens por página).

## Sumário

- [organizations](#organizations) — Organization apis (14 operações)
- [projects](#projects) — Projects apis (6 operações)
- [project](#project) — Project Apis (39 operações)
- [task](#task) — Task Apis (49 operações)
- [chat](#chat) — Chat apis (2 operações)
- [Modelos de dados](#modelos-de-dados)

## organizations

### `GET /organizations`

**Get user organizations**

Respostas: `401` Unauthorized · `200` Success → Organization · `400` Bad request

### `POST /organizations`

**Create organization**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `payload` | body | Create Organization | sim |  |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `PUT /organizations/{organization_id}`

**Update organization**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `organization_id` | path | integer | sim | Id of the organization |
| `payload` | body | Create Organization | sim |  |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `DELETE /organizations/{organization_id}`

**Delete organization**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `organization_id` | path | integer | sim | Id of the organization |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `GET /organizations/{organization_id}/folders`

**Get folders**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `folder_id` | query | string |  | The id of the parent folder |
| `organization_id` | path | integer | sim | Id of the organization |

Respostas: `401` Unauthorized · `200` Success → Folder · `400` Bad request

### `POST /organizations/{organization_id}/folders`

**Create folder**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `folder_id` | query | string |  | The id of the parent folder |
| `organization_id` | path | integer | sim | Id of the organization |
| `payload` | body | Create Folder | sim |  |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `PUT /organizations/{organization_id}/folders/{folder_id}`

**Update folder**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `folder_id` | path | integer | sim | The id of the parent folder |
| `organization_id` | path | integer | sim | Id of the organization |
| `payload` | body | Update Folder | sim |  |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `DELETE /organizations/{organization_id}/folders/{folder_id}`

**Delete folder**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `folder_id` | path | integer | sim | The id of the parent folder |
| `organization_id` | path | integer | sim | Id of the organization |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `PUT /organizations/{organization_id}/folders/{folder_id}/archive`

**Archive folder**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `folder_id` | path | integer | sim | The id of the parent folder |
| `organization_id` | path | integer | sim | Id of the organization |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `GET /organizations/{organization_id}/members`

**Get organization members**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `organization_id` | path | integer | sim | Id of the organization |

Respostas: `401` Unauthorized · `200` Success → Organization Member · `400` Bad request

### `POST /organizations/{organization_id}/members`

**Add organization member**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `organization_id` | path | integer | sim | Id of the organization |
| `payload` | body | Add Organization Member | sim |  |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `GET /organizations/{organization_id}/members/search/{name}`

**Search organization members**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `name` | path | string | sim | Name or username of the member to be searched in the organization |
| `organization_id` | path | integer | sim | Id of the organization |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `DELETE /organizations/{organization_id}/members/{user_id}`

**Remove invited member**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `user_id` | path | integer | sim | The id of the user to be removed from the organization |
| `organization_id` | path | integer | sim | Id of the organization |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `GET /organizations/{organization_id}/projects`

**Get projects in organization**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `organization_id` | path | integer | sim | Id of the organization |

Respostas: `401` Unauthorized · `200` Success → Project · `400` Bad request

## projects

### `GET /projects`

**Get projects**

Respostas: `401` Unauthorized · `200` Success → Project · `400` Bad request

### `POST /projects`

**Create project**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `payload` | body | Create Project | sim |  |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `GET /projects/{project_id}`

**Get project**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `200` Success → Project · `400` Bad request

### `DELETE /projects/{project_id}`

**Delete project**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `PUT /projects/{project_id}`

**Update project**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Project | sim |  |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

### `PUT /projects/{project_id}/archive`

**Archive project**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `200` OK · `400` Bad request

## project

### `GET /projects/tasks/types/icons`

**Get task types icons**

Respostas: `401` Unauthorized · `400` Bad request · `200` Success

### `POST /projects/{project_id}/create_webhook`

**Create or Update a project webhook**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Link Zendesk | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/custom_fields`

**Get project custom fields**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Custom Field

### `POST /projects/{project_id}/custom_fields`

**Create Custom field**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Custom Field | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/custom_fields/{uuid}`

**Update custom field**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `uuid` | path | string | sim |  |
| `payload` | body | Update Custom Field | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/custom_fields/{uuid}`

**Remove custom field**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `uuid` | path | string | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/labels`

**Get labels**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Label

### `POST /projects/{project_id}/labels`

**Create label**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Label | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/labels/{label_id}`

**Update label**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `label_id` | path | integer | sim |  |
| `payload` | body | Update Label | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/labels/{label_id}`

**Delete label**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `label_id` | path | integer | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/lists`

**Get lists**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → List

### `POST /projects/{project_id}/lists`

**Create list**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create List | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/lists/{list_id}`

**List details**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `list_id` | path | integer | sim | Id of the list |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → List

### `DELETE /projects/{project_id}/lists/{list_id}`

**Delete list**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `list_id` | path | integer | sim | Id of the list |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/lists/{list_id}`

**Update list**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `list_id` | path | integer | sim | Id of the list |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update List | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/lists_and_views`

**Lists and view getter**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/members`

**Get project members**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Project Member

### `POST /projects/{project_id}/members`

**Add member**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Add Project Member | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Project Member

### `DELETE /projects/{project_id}/members/{user_id}`

**Remove member**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `user_id` | path | integer | sim | Id of the user |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/milestones`

**Get milestones**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Milestone

### `POST /projects/{project_id}/milestones`

**Create milestone**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Milestone | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/milestones/{milestone_id}`

**put_milestone_actions**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `milestone_id` | path | integer | sim | Id of the milestone |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Milestone | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/milestones/{milestone_id}`

**delete_milestone_actions**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `milestone_id` | path | integer | sim | Id of the milestone |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `POST /projects/{project_id}/pin`

**Pin/Unpin project**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/sprints`

**Get sprints**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Sprint

### `POST /projects/{project_id}/sprints`

**Create sprint**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Sprint | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/sprints/{sprint_id}`

**Get sprint**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `sprint_id` | path | integer | sim | Id of the sprint |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/sprints/{sprint_id}`

**Delete sprint**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `sprint_id` | path | integer | sim | Id of the sprint |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/sprints/{sprint_id}`

**Update sprint**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `sprint_id` | path | integer | sim | Id of the sprint |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Sprint | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/types`

**Get task types**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Type

### `POST /projects/{project_id}/tasks/types`

**Create task type**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Task Type | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/types/{type_id}`

**Get task type**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `type_id` | path | integer | sim | Id of the type |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/types/{type_id}`

**Remove task type**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `type_id` | path | integer | sim | Id of the type |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Delete Task Type | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/types/{type_id}`

**Update task type**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `type_id` | path | integer | sim | Id of the type |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Task Type | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/timers`

**Get project timers**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Timer

### `GET /projects/{project_id}/views`

**Get views**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → ViewModel

### `POST /projects/{project_id}/views`

**Create views**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | CreateViewModel | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/views/{view_id}`

**Update view**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `view_id` | path | integer | sim | Id of the view |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | CreateViewModel | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/views/{view_id}`

**Delete view**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `view_id` | path | integer | sim | Id of the view |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

## task

### `GET /projects/{project_id}/lists/{list_id}/tasks`

**Get tasks in list**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `list_id` | path | integer | sim | Id of the list |
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task

### `POST /projects/{project_id}/lists/{list_id}/tasks`

**Create task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `list_id` | path | integer | sim | Id of the list |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Task | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks`

**Get project tasks**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task

### `GET /projects/{project_id}/tasks/local/{local_id}`

**Get single task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `local_id` | path | integer | sim | Local id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task

### `PUT /projects/{project_id}/tasks/local/{local_id}`

**Update task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `local_id` | path | integer | sim | Local id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Task | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/local/{local_id}/move`

**Move task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `local_id` | path | integer | sim | Local id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Move Task | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}`

**Get single task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task

### `DELETE /projects/{project_id}/tasks/{task_id}`

**Delete task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}`

**Update task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Task | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/activity`

**Get task activity**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `comments_only` | query | boolean |  | True if you want only task activity associated with task comments, false - all the task activity. |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/archive`

**Archive task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/attachments`

**Get attachments**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Attachment

### `POST /projects/{project_id}/tasks/{task_id}/attachments`

**Add attachment**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Add Task Attachement | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/{task_id}/attachments/{attachment_id}`

**Delete attachment**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `attachment_id` | path | integer | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/checklists`

**Get checklists**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Checklist

### `POST /projects/{project_id}/tasks/{task_id}/checklists`

**Create checklist**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Task Checklist | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/{task_id}/checklists/{checklist_id}`

**Delete checklist**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `checklist_id` | path | integer | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/checklists/{checklist_id}/items`

**Get checklist items**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `checklist_id` | path | integer | sim | Id of the checklist |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Checklist

### `POST /projects/{project_id}/tasks/{task_id}/checklists/{checklist_id}/items`

**Create checklist item**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `checklist_id` | path | integer | sim | Id of the checklist |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Task Checklist | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/checklists/{checklist_id}/items/{item_id}`

**Update checklist item**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `item_id` | path | integer | sim | Id of the checklist item |
| `checklist_id` | path | integer | sim | Id of the checklist |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Task Checklist | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/{task_id}/checklists/{checklist_id}/items/{item_id}`

**Delete checklist item**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `item_id` | path | integer | sim | Id of the checklist item |
| `checklist_id` | path | integer | sim | Id of the checklist |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/comments`

**Get comments**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Comment

### `POST /projects/{project_id}/tasks/{task_id}/comments`

**Create comment**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Task Comment | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/comments/{comment_id}`

**Update comment**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `comment_id` | path | integer | sim | Id of the comment |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Task Comment | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/{task_id}/comments/{comment_id}`

**Delete comment**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `comment_id` | path | integer | sim | Id of the comment |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/custom_fields`

**Get task custom fields**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Custom Field

### `POST /projects/{project_id}/tasks/{task_id}/custom_fields`

**Create Task Custom field**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create Task Custom Field | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Custom Field

### `DELETE /projects/{project_id}/tasks/{task_id}/custom_fields/{uuid}`

**Remove custom field**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `uuid` | path | string | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/labels`

**Get labels**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Label

### `POST /projects/{project_id}/tasks/{task_id}/labels/{label_id}`

**Link label to task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `label_id` | path | integer | sim | Id of the label |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/{task_id}/labels/{label_id}`

**Remove label from task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `label_id` | path | integer | sim | Id of the label |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/members`

**Get task assignees**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Member

### `POST /projects/{project_id}/tasks/{task_id}/members`

**Add task assignee**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Add Task Member | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/{task_id}/members/{user_id}`

**Remove task assignee**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `user_id` | path | integer | sim | Id of the user |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/move`

**Move task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Move Task | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/schedules`

**Get schedules**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Schedule

### `POST /projects/{project_id}/tasks/{task_id}/schedules`

**Create schedule**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Create TaskSchedule | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/schedules/{schedule_id}`

**Update schedule**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `schedule_id` | path | integer | sim | Id of the schedule |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Task Schedule | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/{task_id}/schedules/{schedule_id}`

**Remove schedule**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `schedule_id` | path | integer | sim | Id of the schedule |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `POST /projects/{project_id}/tasks/{task_id}/start_timer`

**Start timer**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `POST /projects/{project_id}/tasks/{task_id}/subscribe`

**Watch task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `GET /projects/{project_id}/tasks/{task_id}/timers`

**Get timers**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `offset` | query | string |  | Number of items already displayed |
| `limit` | query | string |  | Number of items per page |

Respostas: `401` Unauthorized · `400` Bad request · `200` Success → Task Timer

### `POST /projects/{project_id}/tasks/{task_id}/timers`

**Create timer**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Add Task Timer | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/timers/{timer_id}`

**Update task timer**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `timer_id` | path | integer | sim | Id of the timer |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `payload` | body | Update Task Timer | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `DELETE /projects/{project_id}/tasks/{task_id}/timers/{timer_id}`

**Delete timer**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `timer_id` | path | integer | sim | Id of the timer |
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/timers/{timer_id}/pause`

**Pause timer**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `timer_id` | path | integer | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/timers/{timer_id}/resume`

**Resume timer**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `timer_id` | path | integer | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `PUT /projects/{project_id}/tasks/{task_id}/timers/{timer_id}/stop`

**Stop timer**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |
| `timer_id` | path | integer | sim |  |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

### `POST /projects/{project_id}/tasks/{task_id}/vote`

**Vote for task**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `task_id` | path | integer | sim | Id of the task |
| `project_id` | path | integer | sim | Id of the project |

Respostas: `401` Unauthorized · `400` Bad request · `200` OK

## chat

### `POST /chat/channel/{channel_id}/message`

**Get all channels for an organization**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `channel_id` | path | integer | sim |  |
| `payload` | body | Send message | sim |  |

Respostas: `401` Unauthorized · `200` Success → Discussion · `400` Bad request

### `GET /chat/{organization_id}`

**Get all channels for an organization**

| Parâmetro | Onde | Tipo | Obrig. | Descrição |
|---|---|---|---|---|
| `organization_id` | path | integer | sim |  |

Respostas: `401` Unauthorized · `200` Success → Discussion · `400` Bad request

## Modelos de dados

### Add Organization Member

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `email` | string | sim | The email of the user to be added in the organization. |

### Add Project Member

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `user` | string | sim | You can add registered user to a project with his email, username or name. |

### Add Task Attachement

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `url` | string | sim | The url of the attachment. |

### Add Task Member

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `user_id` | integer | sim | The id of the user to be assigned to task. |

### Add Task Timer

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `start_date` | string (date-time) | sim | Date and time when the timer was started. |
| `end_date` | string (date-time) | sim | Date and time when the timer has been stoped. |
| `notes` | string |  | Notes for the timer. |

### Create Custom Field

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `name` | string | sim | Title of the custom field. |
| `description` | string |  | Description about the custom field. |
| `type` | integer |  | Type of the custom field (1 - Dropdown, 2 - Number, 3 - Text, 4 - Number, 5 - Date, 6 - Checkbox). |
| `options` | lista de object |  | List with the dropdown options. (It's returned if the type is 1). |
| `is_multiline` | boolean |  | True if the textfield is multiline. (It's returned if the type is 3). |
| `number_format` | integer |  | 1 - Number, 2 - USD, 3 - EUR, 4 - GBP, 5 - YEN, 6 - Percent, 7 - Custom, 8 - Unformatted  (It's returned if the type is 3). |
| `position` | integer |  | 0 - None, 1 - Left, 2 - Right (It's returned if the type is 2). |
| `label` | string |  | Which label to show, Example: %, $. (It's returned if the type is 2). |
| `decimals` | integer |  | (It's returned if the type is 2). |

### Create Folder

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string | sim | The title of the folder. |
| `color` | string | sim | The color of the folder. |

### Create Label

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string | sim | Title of the label |
| `color` | string | sim | Color of the label |

### Create List

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string | sim | Title of the list. |
| `color` | string |  | Color of the list. |
| `list_type` | integer |  | Type of the list. 1 - Open, 2 - Closed, 3 - Review and 4 - Frosen. |
| `public` | boolean |  | If true the list is public, if false - private. |

### Create Milestone

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string | sim | Title of the milestone. |
| `color` | string |  | Color of the milestone. |

### Create Organization

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `name` | string |  | The name of the organization. (Deprecated) This will be ignored |
| `title` | string |  | The name of the organization. |
| `org_type` | integer |  | Type of organization. Two types of constants. 1 - Private and 2 - Public |
| `description` | string |  | Description of the organization. |
| `web` | string |  | Url referencing to the organization. |

### Create Project

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the project. |
| `web` | string |  | Url referencing to the organization. |
| `description` | string |  | Description about the project. |
| `default_view` | boolean |  | True is list, false is kanban. |
| `item_name` | string |  | Name that you want to be used for the tasks in the project. |
| `items_name` | string |  | It is just plural of item_name. |
| `project_color` | string |  | Project color shown in repost or agenda. |

### Create Sprint

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string | sim | Title of the sprint. |
| `duration` | integer | sim | Duration of the sprint in days. |
| `done_list` | integer |  | Counter for completed tasks in the done list. |

### Create Task

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string | sim | Title of the task. |

### Create Task Checklist

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `related_task` | integer | sim | If of the task you want to related to |
| `relation_type` | integer | sim | Type of the relation |

### Create Task Comment

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `data` | string | sim | Content of the comment. |
| `public` | boolean |  | If the field is true, the comment will be team only visible. If false - the comment is public. |

### Create Task Custom Field

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `custom_field_id` | integer |  | Id of the project custom field |
| `date` | string (date) |  | Selected date value. |
| `is_checked` | boolean |  | Id of the selected member. |
| `selected_member` | string |  | List of selected members. |
| `numeric_value` | number |  | Numeric value added to the custom field. |
| `selected_dropdown` | string |  | UUID of the selected dropdown. |
| `text` | string |  | Text of the custom field. |

### Create Task Type

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `name` | string | sim | Name of the task type. |
| `icon` | string | sim | Icon for the task type. |
| `color` | string | sim | The color of the task type. |

### Create TaskSchedule

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `start` | string (date-time) | sim | Date and time when the schedule starts. |
| `end` | string (date-time) | sim | Date and time when the schedule ends. |
| `daily_hours_estimate` | integer | sim | Estimated daily hours |
| `user_id` | integer |  | The id of the user that is voting the task. |

### CreateViewModel

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string | sim | Title of the view. |

### Custom Field

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `uuid` | string |  | UUID of the custom field. |
| `creator_id` | integer |  | Id of the user that created the custom field. |
| `project_id` | integer |  | Id of the project |
| `name` | string |  | Title of the custom field. |
| `description` | string |  | Description about the custom field. |
| `created_at` | string (date-time) |  | Date and time when the custom field is created. |
| `updated_at` | string (date-time) |  | Date and time when the custom field is last updated. |
| `position` | integer |  | 0 - None, 1 - Left, 2 - Right (It's returned if the type is 2). |
| `type` | integer |  | Type of the custom field (1 - Dropdown, 2 - Number, 3 - Text, 4 - Number, 5 - Date, 6 - Checkbox). |
| `options` | lista de object |  | List with the dropdown options. (It's returned if the type is 1). |
| `is_multiline` | boolean |  | True if the textfield is multiline. (It's returned if the type is 3). |
| `number_format` | integer |  | 1 - Number, 2 - USD, 3 - EUR, 4 - GBP, 5 - YEN, 6 - Percent, 7 - Custom, 8 - Unformatted  (It's returned if the type is 3). |
| `label` | string |  | Which label to show, Example: %, $. (It's returned if the type is 2). |
| `decimals` | integer |  | (It's returned if the type is 2). |

### Delete Task Type

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `name` | string | sim | Name of the task type. |
| `icon` | string | sim | Icon for the task type. |
| `color` | string | sim | The color of the task type. |
| `active` | boolean |  | Boolean if the task type is active. |
| `initial` | boolean |  | Boolean if the task type is initial. |

### Discussion

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `id` | integer |  | ID of the channel. |
| `autojoin` | boolean |  | True if new members are added to the channel automatically |
| `archived` | boolean |  | True if the project is archived, if false it is not. |
| `created_at` | string (date-time) |  | Date and time when the channel is created. |
| `last_update` | string |  | Date and time when the channel was last updated. |
| `created_by` | integer |  | ID of the channel creator. |
| `name` | string | sim | Name of the channel. |
| `description` | string | sim | Description of the channel. |
| `picture` | string |  |  |

### Folder

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `parent_id` | integer | sim | If a folder is located into another folder then this parent_id field is the id of that another folder. |
| `personal` | boolean |  | Boolean if the folder is personal. |
| `position` | integer | sim | The position of the folder. |
| `title` | string | sim | The title of the folder. |
| `color` | string | sim | The color of the folder. |
| `privacy` | integer | sim | Folder privacy it can be public(1) or private(2). |
| `folders_count` | integer | sim | Counter for how many folders are in the folder. |
| `projects_count` | integer | sim | Counter for how many projects are in the folder. |

### Label

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string | sim | Title of the label |
| `color` | string | sim | Color of the label |
| `updated_at` | string | sim | Color of the label |
| `archived` | string | sim | Color of the label |

### Link Zendesk

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `url` | string | sim | The webhook URL |
| `task_created` | boolean | sim | Should send a webhook when a task is created. |
| `task_moved` | boolean | sim | Should send a webhook when a task is moved. |
| `task_label_added` | boolean | sim | Should send a webhook when a task label is added. |
| `task_assignee_added` | boolean | sim | Should send a webhook when a task assignee is added. |
| `task_comment_added` | boolean | sim | Should send a webhook when a task comment is added. |
| `task_timer_changed` | boolean | sim | Should send a webhook when a task timer is started or stopped. |

### List

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `view_id` | integer |  | Id of the view where the list is located. |
| `updated_at` | string | sim | Date and time when the list was last updated. |
| `title` | string | sim | Title of the list. |
| `color` | string |  | Color of the list. |
| `list_type` | integer |  | Type of the list. 1 - Open, 2 - Closed, 3 - Review and 4 - Frosen. |
| `archived` | boolean |  | True if the project is archived, if false it is not. |
| `actions` | integer |  | Counter of the list actions. |
| `public` | string |  | If true the list is public, if false - private. |
| `position` | integer |  | Position of the list. |

### Milestone

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the milestone. |
| `created_at` | string (date-time) |  | Date and time when the milestone was created. |
| `updated_at` | string (date-time) |  | Date and time when the milestone was last updated. |
| `archived` | boolean |  | If true the milestone is archived, if false - not archived. |
| `complete` | boolean |  | If true the milestone is completed, if false - not completed. |
| `deadline` | string (date-time) |  | Deadline of the milestone. |
| `color` | string |  | Color of the milestone. |
| `position` | integer |  | Position of the milestone. |

### Move Task

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `list_id` | integer |  | The id of the new list. |

### Organization

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `owner_id` | integer | sim | The id of the user that created the organization. |
| `name` | string | sim | The name of the organization. (Deprecated) |
| `title` | string | sim | The name of the organization. |
| `description` | string | sim | Description of the organization. |
| `created_at` | string (date-time) | sim | Date and time when the organization was created. |
| `updated_at` | string (date-time) | sim | Date and time when the organization was last updated. |
| `org_picture` | string | sim | Organization picture displayed in Ora. Stored in Amazon S3. |
| `org_type` | string | sim | Type of organization. Two types of constants. 1 - Private and 2 - Public. |
| `premium_plan` | string | sim | Shows the plan of the organization. By default it is free and it can be changed to different types of premium(Professional(Professional Year), Startup(Startup year) and Enterprise(Enterprise year)). |
| `quantity` | integer | sim | Counter of members in the organization. |

### Organization Member

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `joined` | string (date-time) | sim | Date and time when the user joined the organization. |
| `leaves` | string (date-time) | sim | Date and time when the user left the organization. |
| `member_type` | integer | sim | The type of the member. 1 - admin and 2 - normal user. |

### Project

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `picture` | string |  | The picture of the project. |
| `organization_id` | string |  | Id of the organization where the project is created. |
| `owner` | string |  | Id of the user that created the project. |
| `title` | string |  | Title of the project. |
| `web` | string |  | Url referencing to the organization. |
| `created_at` | string (date-time) |  | Date and time when the organization was created. |
| `updated_at` | string (date-time) |  | Date and time when the organization was last updated. |
| `description` | string |  | Description about the project. |
| `tasks` | integer |  | Counter of tasks that is used for second id for tasks. In task model there is a second_id field that is this counter. |
| `starred` | integer |  | Counter showing how many people have starred this project. |
| `archived` | boolean |  | True if the project is archived, if false it is not. |
| `default_view` | boolean |  | True is list, false is kanban. |
| `item_name` | string |  | Name that you want to be used for the tasks in the project. |
| `items_name` | string |  | It is just plural of item_name. |
| `project_type` | string |  | Constant about the type of the project. 1 - Private, 2 - Public and 3 - Secret. |
| `comment_all` | string |  | Constant about who can comment in a project. 1 - Members, 2 - Public and 3 - Observers. |
| `commits_visibility` | string |  | Constant about who can see the commits in a project. 1 - Members, 2 - Public and 3 - Observers. |
| `invite_all` | boolean |  | If true then everybody can invite members to the project, if false than not everybody can invite. |
| `project_color` | string |  | Project color shown in repost or agenda. |
| `view_title` | string |  | The title of the default view. |
| `position` | integer |  | Position of the project in a folder. |

### Project Member

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `joined` | string (date-time) | sim | Date and time when the user joined the project. |
| `leaves` | string (date-time) | sim | Date and time when the user left the project. |
| `updated_at` | string (date-time) | sim | Date and time when the project member  was last updated. |
| `user_id` | integer | sim | Id of the user that is a member to the project. |
| `last_list` | integer | sim | Id of the list in the project that was last changed by the member. |
| `last_view` | integer | sim | Id of the view in the project that was last changed by the member. |
| `active` | boolean | sim | If true the user is active, false - inactive. |
| `email` | string | sim | Email of the member. |
| `full_name` | string | sim | Full name of the member(first and last name). |
| `profile_picture` | string | sim | Profile picture of the member. Stored in Amazon S3. |
| `dev_type` | integer | sim | The type of the member. 1 - admin and 2 - regular member. |

### Send message

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `text` | string | sim | Text of the message. |

### Sprint

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the sprint. |
| `created_at` | string (date-time) |  | Date and time when the sprint was created. |
| `updated_at` | string (date-time) |  | Date and time when the sprint was last updated. |
| `start_date` | string (date-time) |  | Date and time when the sprint starts. |
| `end_date` | string (date-time) |  | Date and time when the sprint ends. |
| `duration` | integer |  | Duration of the sprint in days. |
| `done_list` | integer |  | Counter for completed tasks in the done list. |
| `state` | string |  | State of the sprint. |
| `number` | integer |  | Autogenerated. Can not be changed. Number of the sprint. |
| `archived` | boolean |  | False if the project is archived, if false it is not. |
| `tasks` | integer |  | Counter for the tasks in sprint. |
| `tasks_completed` | integer |  | Counter for completed tasks in sprint. |
| `points` | integer |  | Effort estimate in points. Every task has Story points. They are combined. |
| `points_completed` | integer |  | Completed Story points in the sprint. |
| `value` | integer |  | Business value estimate of the sprint. Every task has business value points. They are combined. |
| `value_completed` | integer |  | Completed Business value points in the sprint. |

### Task

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `milestone_id` | integer |  | Id of the milestone in the task(milestone can be attached to the task). |
| `task_type` | integer |  | Id of the task type(show what type is the task - bug, feature, etc.). |
| `creator` | integer |  | Id of the user that created the task. |
| `second_id` | integer |  | Id that is equal to tasks counter in Project model. It is shown when you click the task under the task title(#10, #11, etc.). |
| `title` | string |  | Title of the task. |
| `description` | string |  | Description about the task. |
| `last_picture` | string |  | Last picture that is uploaded to the task through Ora. |
| `last_picture_external_url` | string |  | Last picture that is uploaded to the task through external service(Trelo, etc.). |
| `created_at` | string (date-time) |  | Date and time when the project was created. |
| `updated_at` | string (date-time) |  | Date and time when the project was last updated. |
| `deadline` | string (date-time) |  | Deadline of the task. |
| `archived` | boolean |  | True if the task is archived, if false it is not. |
| `color` | string |  | Color of the task. |
| `estimated` | string |  | Estimated time for completing the task. |
| `time_tracked` | string |  | Time that is tracked while working on the task. |
| `public` | boolean |  | True if the task has to be public, false if it should not. By default it is true(public). |
| `state` | integer |  | The state of the task. 1 - Frosen, 2 - Open, 3 - Review, 4 - Closed. |
| `cover_width` | integer |  | Width of the task. |
| `cover_height` | integer |  | Height of the task. |
| `checklist` | string |  | Counter for how many points of the checklist in the task are completed. Completed points are on the left and total points are on the right(2/5, 1/5, 5/5, etc.). |
| `comments` | integer |  | Counter for comments on a task. |
| `public_comments` | integer |  | Counter for public comments on a task. |
| `likes` | integer |  | Counter for likes on a task. |
| `attachments` | integer |  | Counter for attachments on a task. |
| `commits` | integer |  | Counter for commits on a task. |
| `support_tickets` | integer |  | Counter for support tickets on a task. |
| `value` | integer |  | Business value of the task. What importance for the business it has. |
| `points` | integer |  | Difficulty of the task. How many points in the task there are to be done. |
| `points_done` | integer |  | Counter for how many points are done. |
| `sprint_id` | integer |  | Id of the sprint in which is the task. |
| `position` | integer |  | Position of the task in the sprint. |

### Task Attachment

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `upload_date` | string (date-time) |  | The picture of the project. |
| `data_path` | string |  | Path of the uploaded data. |
| `external_url` | string |  | Path of the uploaded data if the attachment is not uploaded from Ora but from external service. |
| `file_title` | string |  | Title of the file that is uploaded. |
| `file_size` | string |  | Size of the file uploaded. |
| `file_type` | string |  | Type of the file uploaded. |
| `picture_width` | integer |  | Width of the attachment if it is a picture. |
| `picture_height` | integer |  | Height of the attachment if it is a picture. |
| `activity_id` | integer |  | Description about the project. |

### Task Checklist

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `main_id` | integer |  | If the checklist is a item to another checklist then this main_id will be the id of the parent checklist. |
| `title` | string |  | Title of the checklist. |
| `deadline` | string (date-time) |  | Date and time when the deadline for completing the checklist is. |
| `total_time` | integer |  | Total time spent working on the checklist. |
| `checked` | boolean |  | If this checklist is a item to another checklist then when it is completed it will be checked(true) which means it is done. |
| `position` | integer |  | Position of the checklist. |

### Task Comment

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `comment` | string | sim | Content of the comment. |
| `created_at` | string (date-time) |  | Date and time when the comment was created. |
| `updated_at` | string (date-time) |  | Date and time when the comment was last updated. |
| `public` | boolean |  | If the field is true, the comment will be team only visible. If false - the comment is public. |

### Task Custom Field

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `uuid` | string |  | UUID of the custom field. |
| `creator_id` | integer |  | Id of the user that created the custom field. |
| `task_id` | integer |  | Id of the task |
| `project_id` | integer |  | Id of the project |
| `custom_field_id` | integer |  | Id of the project custom field |
| `name` | string |  | Title of the custom field. |
| `created_at` | string (date-time) |  | Date and time when the custom field is created. |
| `updated_at` | string (date-time) |  | Date and time when the custom field is last updated. |
| `date` | string (date) |  | Selected date value. |
| `is_checked` | boolean |  | Id of the selected member. |
| `selected_member` | string |  | List of selected members. |
| `numeric_value` | number |  | Numeric value added to the custom field. |
| `selected_dropdown` | string |  | UUID of the selected dropdown. |
| `text` | string |  | Text of the custom field. |

### Task Label

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `label_id` | integer |  | Id of the label that is added to the task. |
| `created_at` | string (date-time) |  | Date and time when the label was added to the task. |
| `updated_at` | string (date-time) |  | Date and time when the label was last updated. |
| `archived` | boolean |  | True if the label is archived, if false it is not. |
| `deleted` | boolean |  | True if the label is deleted, if false it is not. |

### Task Member

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `user_id` | integer |  | Id of the user that is assigned to the task. |
| `joined` | string (date-time) |  | Date and time when the user was assigned to the task. |
| `archived` | boolean |  | The id of the user to be assigned to task. |
| `deleted` | boolean |  | True if the assignee is deleted, if false it is not. |
| `updated_at` | string (date-time) |  | Date and time when the assignee was last updated. |

### Task Schedule

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `user_id` | integer |  | The id of the user that is voting the task. |
| `start` | string (date-time) |  | Date and time when the schedule starts. |
| `end` | string (date-time) |  | Date and time when the schedule ends. |
| `estimate` | integer |  | Estimated time for completing the schedule. In hours. |
| `daily_estimate` | integer |  | Estimated time for working daily on the schedule. In hours. |
| `deleted` | boolean |  | True if the schedule is deleted, if false it is not. |
| `updated_at` | string (date-time) |  | Date and time when the schedule was last updated. |

### Task Timer

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `user_id` | integer |  | Id of the user that started the timer. |
| `checklist_id` | integer |  | If the timer is started on a checklist then checklist_id is the id of that checklist. |
| `task_title` | string |  | Title of the task where the timer is started. |
| `status` | string |  | Status of the timer. |
| `created_at` | string (date-time) |  | Date and time when the timer was created. |
| `total` | string |  | Total time the timer tracked. |
| `last_time` | string |  | Time spent last time. |
| `ended_at` | string (date-time) |  | Date and time when the timer has been stopped. |
| `archived` | boolean |  | True if the timer is archived |
| `notes` | string |  | Notes for the timer. |

### Task Type

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `name` | string |  | Name of the task type. |
| `icon` | string |  | Icon for the task type. |
| `color` | string |  | The color of the task type. |
| `active` | boolean |  | Boolean if the task type is active. |
| `initial` | boolean |  | Boolean if the task type is initial. |
| `archived` | boolean |  | True if the task type is archived, if false it is not. |

### Update Custom Field

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `name` | string |  | Title of the custom field. |
| `description` | string |  | Description about the custom field. |
| `position` | number |  | Position of the custom field. |
| `options` | lista de object |  | List with the dropdown options. (It's returned if the type is 1). |
| `is_multiline` | boolean |  | True if the textfield is multiline. (It's returned if the type is 3). |
| `number_format` | integer |  | 1 - Number, 2 - USD, 3 - EUR, 4 - GBP, 5 - YEN, 6 - Percent, 7 - Custom, 8 - Unformatted  (It's returned if the type is 3). |
| `label_position` | integer |  | 0 - None, 1 - Left, 2 - Right (It's returned if the type is 2). |
| `label` | string |  | Which label to show, Example: %, $. (It's returned if the type is 2). |
| `decimals` | integer |  | (It's returned if the type is 2). |

### Update Folder

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | The title of the folder. |
| `color` | string |  | The color of the folder. |

### Update Label

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the label |
| `color` | string |  | Color of the label |

### Update List

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the list. |
| `color` | string |  | Color of the list. |
| `list_type` | integer |  | Type of the list. 1 - Open, 2 - Closed, 3 - Review and 4 - Frosen. |
| `position` | integer |  | Position of the list. |
| `actions` | integer |  | Counter of the list actions. |
| `public` | string |  | If true the list is public, if false - private. |

### Update Milestone

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the milestone. |
| `color` | string |  | Color of the milestone. |
| `complete` | boolean |  | If true the milestone is completed, if false - not completed. |
| `position` | integer |  | Position of the milestone. |

### Update Sprint

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the sprint. |
| `duration` | integer |  | Duration of the sprint in days. |
| `done_list` | integer |  | Counter for completed tasks in the done list. |
| `start_date` | string (date-time) |  | Date and time when the sprint starts. |
| `end_date` | string (date-time) |  | Date and time when the sprint ends. |
| `state` | string |  | State of the sprint. |

### Update Task

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the task. |
| `color` | string |  | Color of the task. |
| `task_type` | integer |  | Id of the task type(show what type is the task - bug, feature, etc.). |
| `position` | integer |  | Position of the task in the sprint. |
| `points` | integer |  | Difficulty of the task. How many points in the task there are to be done. |
| `points_done` | integer |  | Counter for how many points are done. |
| `state` | integer |  | The state of the task. 1 - Frosen, 2 - Open, 3 - Review, 4 - Closed. |
| `estimated` | string |  | Estimated time for completing the task. |
| `deadline` | string (date-time) |  | Deadline of the task. |
| `value` | integer |  | Business value of the task. What importance for the business it has. |
| `description` | string |  | Description about the task. |
| `milestone_id` | integer |  | Id of the milestone in the task(milestone can be attached to the task). |

### Update Task Checklist

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `title` | string |  | Title of the checklist. |
| `deadline` | string (date-time) |  | Date and time when the deadline for completing the checklist is. |
| `total_time` | integer |  | Total time spent working on the checklist. |
| `checked` | boolean |  | If this checklist is a item to another checklist then when it is completed it will be checked(true) which means it is done. |

### Update Task Comment

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `data` | string | sim | Content of the comment. |

### Update Task Schedule

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `user_id` | integer |  | The id of the user that is voting the task. |
| `start` | string (date-time) |  | Date and time when the schedule starts. |
| `end` | string (date-time) |  | Date and time when the schedule ends. |
| `estimate` | integer |  | Estimated time for completing the schedule. In hours. |

### Update Task Timer

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `start_date` | string (date-time) |  | Date and time when the timer was started. |
| `end_date` | string (date-time) |  | Date and time when the timer has been stoped. |
| `notes` | string |  | Notes for the timer. |

### Update Task Type

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `name` | string | sim | Name of the task type. |
| `icon` | string | sim | Icon for the task type. |
| `color` | string | sim | The color of the task type. |
| `active` | boolean |  | Boolean if the task type is active. |
| `initial` | boolean |  | Boolean if the task type is initial. |

### ViewModel

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `type` | integer |  | Type of the view. 0 - Custom and 1 - Sprint. |
| `updated_at` | string (date-time) |  | Date and time when the view was last updated. |
| `title` | string |  | Title of the view. |
| `active` | boolean |  | If true the view is active, if false - inactive. |
| `position` | integer |  | Positionof the view. |
