# Тест агента

В `.env` проекта MCP добавь `QWEN_API_KEY`. При необходимости задай
`MODEL_SLEEP_AI` (по умолчанию `qwen3.7-plus`) и `MCP_URL`
(по умолчанию `http://localhost:8800/mcp`).

Агент и сервер используют MCP SDK 2.2.0 в общей корневой `.venv`.
Интеграция — `langchain.mcp.MCPAdapter` и `ToolNode`.
Модель вызывается через `langchain_openai.ChatOpenAI` с OpenAI-совместимым
endpoint Qwen. `DASHSCOPE_API_BASE` позволяет переопределить адрес API.
`ChatQwQ` не используется: установленная версия изменяет отдельные фрагменты
потоковых аргументов через JSON repair и может потерять последнюю цифру даты.

Установка зависимостей:

```sh
uv pip install --python .venv/bin/python -r tests/requirements.txt
```

Самостоятельно запусти MCP в отдельном терминале из корня проекта:

```sh
.venv/bin/python server.py
```

Затем запусти агента из корня проекта:

```sh
python -m tests.agent
```

Агент только подключается к указанному HTTP-адресу.
Порт веб-интерфейса Inspector тоже не является MCP endpoint.

ID и запрос меняются внизу `tests/agent.py`. Промпты читаются из
`../st_artificial_intelligence/app/sleep_ai/context/main`.
В логах видны выбранные моделью инструменты, аргументы, результаты и ответ.

Проверка сборки даты из потоковых фрагментов без обращения к API:

```sh
.venv/bin/python -m unittest tests.test_tool_stream
```
