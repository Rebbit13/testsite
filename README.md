This is my first site on python
---
I try to build an app for a flower store. It should contain auth, personal account, list of products, blog 
and some other features.

What I use
---
- FastApi
- Pydantic
- Uvicorn
- Sqlite3

Modules
---
- main - process requests to a server
  * "/web/api/token" - the path to register a user session. The wed app gets token and session id to 
    send in further requests and links them to a session
  * "/web/api/registration" - the path to register new customer by name, telephone, password
  * "/web/api/auth" - the path to auth, links the user session to a register customer
    
- models - contain classes to verify and send to a db
  * Session - user session 
  * Customer - registered customer
    
- db_connection - module to communicate with db