# TestBuddy 
your Behaviour driven development (BDD) friendly test management tool

### General information
- automation testing and integration with the CI/CD tool Gitlab CI (and a possibility of adding more integrations)
- test library management (test plans, test cases, test steps)
- JBehave BDD framework support (and a possibility of adding more integrations)
- requirements management
- test reporting
- issue generation and grouping based on failing reports
- integration of the issue tracker JIRA  (and a possibility of adding more integrations)


Please find further details in project's documentation in  `backend/doc` folder.

###Manual

####Prerequisites
Application is multiplatform, but it is recommended to use Windows type of an operation system. Users need to have [Docker](https://www.docker.com/) and a modern web browser installed on their local machine. In case of Linux system, *docker* and *docker-compose* are necessary dependencies.
####Deployment
A user is expected to use following commands to correctly start TestBuDDy (its containers for the backend, the database and tests) from this `src/` folder.
- `docker-compose build` - first, the docker containers have to be built.
- `docker-compose up` - to start TestBuDDy and run tests; in case when the user wants to not only start the application, but also execute its unit tests (for endpoints)

- `docker-compose down` - to stop the application and destroy the containers.
- `docker-compose up backend` - to only start TestBuDDy application (with no changes on the database).
- `docker-compose up --build ` - to start TestBuDDy, run tests and build the application containers in one command

User can view all REST API endpoints in *Swagger API documentation* on `root_url` of the project, which is set to [127.0.0.1:5000](). An example of the Swagger documentation and an example of available endpoints are visible in documentation. Swagger allows user to test every endpoint and defines expected results of a request call. Is is also possible to use API development tool [Postman](https://www.getpostman.com/), alternatively [cUrl](https://curl.haxx.se/) CLI tool.

####Demo initialisation
#####Test Library
For demonstrative purposes, there is an **initialising endpoint** (POST type of a request) provided:
[127.0.0.1:5000/init-data]()
    
2 active public project repositories are already set up for the user when working with their test library:
1. [https://pajda.fit.vutbr.cz/testos/testbuddy-sut]()
1. [https://pajda.fit.vutbr.cz/xblozo00/testing_repo]()

Upon the creation of both projects, TestBuDDy uses the Gitlab CI generated token, that will be available for next few months.
It is also recommended to first initialise your projects' repository by the following endpoint of a POST type:
[127.0.0.1:5000/projects/<proj_id>/init_repo]()
The project has its test library already created until the test case level (in the database layer), so a user can view current test cases and add a new scenario of their choice, or,if preferred, create their own test cases and so on.
#####Test Run Management and Gitlab CI
The repositories were already used in the past, so when working with its test run library, there are also historic pipeline records and reports processed and shown. These records are shown when synchronising with Gitlab CI by calling an endpoint of a POST type:
    [127.0.0.1:5000/projects/<proj_id>/ci_runs/sync]()
#####Requirement Management
Requirements and tags were also created, so user is free to manage them, connect them with existing test cases etc.
#####Incident Management and JIRA Integration}
For the purpose of TestBuDDy demonstration of incident management, JIRA page was created: [TestBuDDy JIRA](https://tesbuddy.atlassian.net/).
User can log in using these credentials: 

 Field | Input
------------ | -------------
username| *testbuddyBUT@gmail.com*
password |  *gherkinisawesome*

