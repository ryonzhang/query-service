## Query Service

This repository serves as a convenience strategy for data engineers or potentially backend engineers to create backend services without backend code. As all the backend services nowadays are somehow manipulating the user request and parsing them into some query language and retrieve the information from persistent layer. Since postgres is the prevalent option for persistent layer and SQL is the dominant language in query domain. This repository offers a new way to create the endpoints without codebase change by directly registering paths with query statements.

## Table of Contents
- [Query Service](#query-service)
  * [How to Run this Project](#how-to-run-this-project)
  * [Endpoints to Query](#endpoints-to-query)
  * [Register Endpoints to Query](#register-endpoints-to-query)
  * [Retrieve the path list](#retrieve-the-path-list)
  * [Collision Detection](#collision-detection)
  * [Caution and Comment](#caution-and-comment)
  
### How to Run this Project
`python server.py`

### Endpoints to Query
For example, the table schema displays itself as below:
row | loan_id | transaction_id | user_id | amount | fee | currency | product_id | paid_at | created_at | updated_at | due_at | status | channel | uuid
--- | --- | --- | --- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |---
0 | 12 | b12296516088492e155501ac2d918352 | 1 | 25.0 | 2.0 | INR | credit_1 | NaT | 2019-12-03  19:45:39.538371 | 2019-12-03  19:45:40.481586 | 2020-01-02 23:59:59 | 2 |  | a6f5936294f04038aa610d8aa1e2bf25
1 | 1 | 1166c6d799aa9198c63f3320f3779ece | 1 | 10.0 | 2.0 | INR | credit_1 | 2019-08-28 06:32:23 | 2019-08-27 10:02:38.271124 | 2019-08-28 06:32:28.543013 | 2019-08-27 23:59:59 | 1 | ussd | a6f5936294f04038aa610d8aa1e2bf25
2 | 46 | 8943c895ec18928a3898e8e63f85c28c | 2 | 10.0 | 2.0 | INR | credit_1 | NaT | 2020-02-26 17:02:28.847831 | 2020-02-26 17:02:31.263454 | 2020-03-27 23:59:59 | 2 |  | f8ef33f721ec4a4aba877dc068d2f1dd

In order to query the user_id, amount and fee of the loans:

`GET http://localhost:5000/query`
```json
{
    "query":"SELECT user_id,amount,fee FROM bsnl.bsnl_lend_loans ORDER BY updated_at DESC LIMIT 3"
}
```
Response:
```json
[
    {
        "user_id": 100546,
        "amount": 10.0,
        "fee": 2.0
    },
    {
        "user_id": 100540,
        "amount": 10.0,
        "fee": 2.0
    },
    {
        "user_id": 100429,
        "amount": 20.0,
        "fee": 4.0
    }
]
```
In order to query the match as hour, count and sum for exposure

`GET http://localhost:5000/query`
```json
{
    "query":"SELECT EXTRACT(HOUR FROM created_at) AS match,COUNT(*) ,SUM(amount) FROM bsnl.bsnl_lend_loans WHERE paid_at IS NULL AND due_at>GETDATE() GROUP BY match ORDER BY match;"
}
```
Response:
```
[
    {
        "match": 0,
        "count": 505,
        "sum": 7450.0
    },
    {
        "match": 1,
        "count": 742,
        "sum": 11510.0
    },
    {
        "match": 2,
        "count": 928,
        "sum": 14400.0
    },
    {
        "match": 3,
        "count": 1191,
        "sum": 18030.0
    },
    {
        "match": 4,
        "count": 1509,
        "sum": 23210.0
    },
    ...
    {
        "match": 21,
        "count": 47,
        "sum": 740.0
    },
    {
        "match": 22,
        "count": 61,
        "sum": 930.0
    },
    {
        "match": 23,
        "count": 159,
        "sum": 2540.0
    }
]
```
### Register Endpoints to Query
As a shortcut to retrieve certain information as the conventional endpoints, we don't want to pass in query everytime we need it. We can register the endpoint to certain endpoint for later recall.

For example, if we want to attach an endpoint for query `SELECT EXTRACT(HOUR FROM created_at) AS match,COUNT(*) redshift_count,SUM(amount) redshift_amount FROM bsnl.bsnl_lend_loans WHERE paid_at IS NULL AND due_at>GETDATE() GROUP BY match` to endpoint `exposure/bsnl/hour`

`GET http://localhost:5000/register`
```json
{
    "path":"exposure/bsnl/hour",
    "query":"SELECT EXTRACT(HOUR FROM created_at) AS match,COUNT(*) redshift_count,SUM(amount) redshift_amount FROM bsnl.bsnl_lend_loans WHERE paid_at IS NULL AND due_at>GETDATE() GROUP BY match;"
}
```
If there is a clash with exising paths registered, it will return `conflict with path(s) {...}` otherwise `ok`

Once registered, you can ping `GET http://localhost:5000/path/exposure/bsnl/hour` which generates the same results as you put the query in the body.

Sometimes, we need to generalise certain path like to retrieve the information by passing the user_id in the path, to resolve this, wildcards can be registered in the paths like below:

For example, if we want to retrieve certain number of ussd_sessions based on the params in the path, we can register the path like below:

`GET http://localhost:5000/register`
```json
{
    "path":"ussd_session/<number>",
    "query":"SELECT * FROM bsnl.ussd_sessions LIMIT <number>;"
}
```
Upon being successfully registered, by calling `GET http://localhost:5000/path/ussd_session/2`

Response
```json
[
    {
        "uuid": "ebd02c1d28494400883873e8bf381ddc",
        "date": 1592265600000,
        "execution_date": 1592265600000
    },
    {
        "uuid": "4b71e20112474e7292195eef881024a6",
        "date": 1592265600000,
        "execution_date": 1592265600000
    }
]
```
### Retrieve the Path List 
We may need to list all the registered paths by calling `GET http://localhost:5000/paths`

Response:
```json
{
    "ussd_session/<number>": "SELECT * FROM bsnl.ussd_sessions LIMIT <number>;",
    "exposure/bsnl/hour": "SELECT EXTRACT(HOUR FROM created_at) AS match,COUNT(*) redshift_count,SUM(amount) redshift_amount FROM bsnl.bsnl_lend_loans WHERE paid_at IS NULL AND due_at>GETDATE() GROUP BY match;"
}
```

### Collision Detection
When registering new paths, duplication should be avoided by all means especially when there is the option of wildcards. For example, path `ussd_session/<number>` will be in conflict with `ussd_session/8` or `ussd_session/blablu`.

This is solved by pattern matching back and forth between the path to add and the existing paths, once collision detected, it will render `conflict with path(s) {...}`

### Caution and Comment
1. This service `/query` endpoint is supposed to use internally which means it is a micro-service used inside our clusters and forbidden to be directly accessed by clients or external parties, because data leakage could occur, however registerd paths should be okay if the external party is authorized.
2. This service should either couple with service account with readonly access user previlege (SELECT) to the database to reduce the risk for internal users, or grant some other endpoints with more previleges to certain experienced users.
3. Even SQL query would be ideally more efficient than the conventional approach of preprocessing by backend code and translating to many query statement and then passing it to database, we should limit the rate of the access of this service account or dedicate a read-replica to this service
4. The performance of a pure query requires more expertise in SQL construction,as SQL is very powerful language, it should be sufficient in most cases to query data. However whether to use this approach over the traditional ORM approach, we should also concern the factors including code maintenance, performance, efficiency, etc. Ideally this should be used only by data engineers to conveniently create a backend service without resorting to a lot of errands of different micro-service creation.  
