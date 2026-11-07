"""Role competency catalog and verified educational URLs for demo search.

Demo resources are predefined real pages. They are never labelled as live search.
"""

from __future__ import annotations

DISCLAIMER = (
    "Self-reported levels are what you entered. Priority and gap labels compare those "
    "entries with a role rubric. They are not an objective or verified measure of competence."
)
RUBRIC_VERSION = "importance-x-gap-v1"

ALIASES = {
    "js": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "node.js": "javascript",
    "react.js": "react",
    "reactjs": "react",
    "postgres": "sql",
    "postgresql": "sql",
    "mysql": "sql",
    "sqlite": "sql",
    "py": "python",
    "html": "html and css",
    "css": "html and css",
    "html/css": "html and css",
    "ts": "typescript",
    "k8s": "kubernetes",
    "sklearn": "machine learning",
    "ml": "machine learning",
    "rest": "http apis",
    "rest api": "http apis",
    "apis": "http apis",
    "api design": "http apis",
    "go lang": "go",
    "golang": "go",
}

ROLE_ALIASES = {
    "backend": "backend engineer",
    "backend developer": "backend engineer",
    "backend engineer": "backend engineer",
    "python developer": "backend engineer",
    "server engineer": "backend engineer",
    "frontend": "frontend engineer",
    "frontend developer": "frontend engineer",
    "frontend engineer": "frontend engineer",
    "react developer": "frontend engineer",
    "ui engineer": "frontend engineer",
    "full stack": "full stack engineer",
    "full stack developer": "full stack engineer",
    "full stack engineer": "full stack engineer",
    "fullstack engineer": "full stack engineer",
    "fullstack developer": "full stack engineer",
    "data analyst": "data analyst",
    "analytics": "data analyst",
    "business analyst": "data analyst",
    "data scientist": "data scientist",
    "ml engineer": "machine learning engineer",
    "machine learning engineer": "machine learning engineer",
    "mle": "machine learning engineer",
    "ai engineer": "machine learning engineer",
    "devops": "devops engineer",
    "devops engineer": "devops engineer",
    "sre": "devops engineer",
    "site reliability engineer": "devops engineer",
    "qa": "qa engineer",
    "qa engineer": "qa engineer",
    "test engineer": "qa engineer",
    "sdet": "qa engineer",
    "software engineer": "software engineer",
    "software developer": "software engineer",
    "swe": "software engineer",
}


def _c(name: str, importance: int, target: int, why: str) -> dict:
    return {"name": name, "importance": importance, "target_level": target, "why": why}


CATALOG: dict[str, dict] = {
    "backend engineer": {
        "title": "Backend Engineer",
        "competencies": [
            _c("Python", 5, 4, "Most backend services, scripts, and APIs in this path are built in Python."),
            _c("SQL", 5, 4, "Product features depend on correct relational queries and schema design."),
            _c("HTTP APIs", 5, 4, "Backend work is largely designing and debugging HTTP interfaces."),
            _c("Testing", 4, 3, "Tests keep API changes from breaking clients and data writes."),
            _c("Git", 3, 3, "You need a reliable way to review, branch, and ship code with others."),
            _c("Docker", 3, 3, "Services are usually run and deployed as containers."),
        ],
    },
    "frontend engineer": {
        "title": "Frontend Engineer",
        "competencies": [
            _c("HTML and CSS", 5, 4, "Layout, semantics, and styling are the base of every interface."),
            _c("JavaScript", 5, 4, "Browser behavior and application logic are written in JavaScript."),
            _c("React", 5, 4, "React is the component model expected for this target role."),
            _c("TypeScript", 4, 3, "Typed components catch API and state mistakes before runtime."),
            _c("Accessibility", 4, 3, "Interfaces need to work with keyboard and assistive technology."),
            _c("Testing", 3, 3, "UI tests protect critical user flows when components change."),
        ],
    },
    "full stack engineer": {
        "title": "Full Stack Engineer",
        "competencies": [
            _c("JavaScript", 5, 4, "Full stack roles use JavaScript on the client and often the server."),
            _c("React", 4, 3, "The interface layer is commonly built with React."),
            _c("Python", 4, 3, "Python is a practical language for APIs and data handling."),
            _c("SQL", 5, 4, "You will model data and write the queries behind product features."),
            _c("HTTP APIs", 5, 4, "The client and server meet at HTTP contracts."),
            _c("Git", 3, 3, "Shipping across the stack requires disciplined version control."),
        ],
    },
    "data analyst": {
        "title": "Data Analyst",
        "competencies": [
            _c("SQL", 5, 4, "Analysts answer questions by querying warehouse tables directly."),
            _c("Statistics", 5, 4, "Conclusions need basic uncertainty, aggregation, and comparison skills."),
            _c("Python", 4, 3, "Python is used to clean data and repeat analyses."),
            _c("Data visualization", 4, 3, "Stakeholders understand results through clear charts."),
            _c("Spreadsheets", 3, 3, "A lot of business data still arrives and is checked in spreadsheets."),
            _c("Communication", 4, 3, "An analysis is useful only if the decision is stated clearly."),
        ],
    },
    "data scientist": {
        "title": "Data Scientist",
        "competencies": [
            _c("Python", 5, 4, "Modeling and data preparation are done primarily in Python."),
            _c("Statistics", 5, 4, "Model claims depend on statistical reasoning."),
            _c("Machine learning", 5, 4, "The role is expected to train and evaluate predictive models."),
            _c("Pandas", 4, 4, "Tabular data wrangling is daily work."),
            _c("SQL", 4, 3, "Training data is usually extracted from relational stores."),
            _c("Experimentation", 3, 3, "You need to compare models and product changes honestly."),
        ],
    },
    "machine learning engineer": {
        "title": "Machine Learning Engineer",
        "competencies": [
            _c("Python", 5, 4, "Training code, services, and tooling are Python-first."),
            _c("Machine learning", 5, 4, "You need to select, train, and evaluate models."),
            _c("Deep learning", 4, 3, "Many applied roles expect a neural-net baseline."),
            _c("SQL", 3, 3, "Feature data is pulled from production databases."),
            _c("Docker", 4, 3, "Models are packaged and run as services."),
            _c("Testing", 3, 3, "Data and prediction tests catch silent training breakage."),
        ],
    },
    "devops engineer": {
        "title": "DevOps Engineer",
        "competencies": [
            _c("Linux", 5, 4, "Servers, logs, and automation are operated from Linux shells."),
            _c("Git", 4, 3, "Infrastructure and application changes are reviewed in Git."),
            _c("Docker", 5, 4, "Containers are the unit of build and deployment."),
            _c("CI/CD", 5, 4, "The role owns repeatable build and release pipelines."),
            _c("Kubernetes", 4, 3, "Teams commonly schedule containers with Kubernetes."),
            _c("Cloud fundamentals", 4, 3, "Workloads run on a cloud account you must navigate safely."),
        ],
    },
    "qa engineer": {
        "title": "QA Engineer",
        "competencies": [
            _c("Testing", 5, 4, "Test design is the core of the role."),
            _c("Test automation", 5, 4, "Regression coverage has to run without manual repetition."),
            _c("HTTP APIs", 4, 3, "Many defects are found at API boundaries."),
            _c("SQL", 3, 3, "You will check persisted state, not only the UI."),
            _c("Git", 3, 3, "Automated tests live in the same review flow as product code."),
            _c("CI/CD", 3, 3, "Tests need to run on every change."),
        ],
    },
    "software engineer": {
        "title": "Software Engineer",
        "competencies": [
            _c("Python", 4, 3, "A general programming language is required to build and automate."),
            _c("Git", 4, 3, "Collaboration depends on branches, commits, and reviews."),
            _c("SQL", 4, 3, "Most products store state in a relational database."),
            _c("HTTP APIs", 4, 3, "Services communicate over HTTP."),
            _c("Testing", 4, 3, "Changes need a repeatable check before they ship."),
            _c("Problem solving", 3, 3, "You will break unfamiliar tasks into debuggable steps."),
        ],
    },
}

RESOURCES: dict[str, list[dict[str, str]]] = {
    "Python": [
        {"title": "Python tutorial", "url": "https://docs.python.org/3/tutorial/", "snippet": "Official Python language tutorial."},
        {"title": "Python standard library", "url": "https://docs.python.org/3/library/index.html", "snippet": "Official index of the Python standard library."},
    ],
    "SQL": [
        {"title": "PostgreSQL tutorial", "url": "https://www.postgresql.org/docs/current/tutorial.html", "snippet": "Official PostgreSQL introduction and SQL tutorial."},
        {"title": "PostgreSQL SQL language", "url": "https://www.postgresql.org/docs/current/tutorial-sql.html", "snippet": "Official chapter on SQL statements in PostgreSQL."},
    ],
    "HTTP APIs": [
        {"title": "MDN HTTP overview", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview", "snippet": "MDN reference for how HTTP works."},
        {"title": "FastAPI tutorial", "url": "https://fastapi.tiangolo.com/tutorial/", "snippet": "FastAPI's official user guide for building APIs."},
    ],
    "Testing": [
        {"title": "pytest getting started", "url": "https://docs.pytest.org/en/stable/getting-started.html", "snippet": "Official pytest introduction."},
        {"title": "Python unittest", "url": "https://docs.python.org/3/library/unittest.html", "snippet": "Official unittest documentation."},
    ],
    "Git": [
        {"title": "Git tutorial", "url": "https://git-scm.com/docs/gittutorial", "snippet": "Official introductory Git tutorial."},
        {"title": "About Git (GitHub Docs)", "url": "https://docs.github.com/en/get-started/using-git/about-git", "snippet": "GitHub's explanation of Git in a team workflow."},
    ],
    "Docker": [
        {"title": "Docker get started", "url": "https://docs.docker.com/get-started/", "snippet": "Official Docker walkthrough."},
        {"title": "Docker overview", "url": "https://docs.docker.com/get-started/docker-overview/", "snippet": "Official overview of images and containers."},
    ],
    "HTML and CSS": [
        {"title": "Learn HTML", "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML", "snippet": "MDN structured HTML learning guide."},
        {"title": "Learn CSS", "url": "https://developer.mozilla.org/en-US/docs/Learn/CSS", "snippet": "MDN structured CSS learning guide."},
    ],
    "JavaScript": [
        {"title": "JavaScript guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "snippet": "MDN JavaScript guide."},
        {"title": "JavaScript.info", "url": "https://javascript.info/", "snippet": "Long-form JavaScript tutorial from fundamentals through the browser."},
    ],
    "React": [
        {"title": "Quick start", "url": "https://react.dev/learn", "snippet": "Official React learning guide."},
        {"title": "Thinking in React", "url": "https://react.dev/learn/thinking-in-react", "snippet": "Official React guide to breaking a UI into components."},
    ],
    "TypeScript": [
        {"title": "TypeScript in 5 minutes", "url": "https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html", "snippet": "Official short TypeScript handbook introduction."},
        {"title": "TypeScript handbook", "url": "https://www.typescriptlang.org/docs/handbook/intro.html", "snippet": "Official TypeScript handbook."},
    ],
    "Accessibility": [
        {"title": "Learn accessibility", "url": "https://developer.mozilla.org/en-US/docs/Learn/Accessibility", "snippet": "MDN accessibility learning module."},
        {"title": "WAI fundamentals", "url": "https://www.w3.org/WAI/fundamentals/", "snippet": "W3C Web Accessibility Initiative fundamentals."},
    ],
    "Statistics": [
        {"title": "Statistics and probability", "url": "https://www.khanacademy.org/math/statistics-probability", "snippet": "Khan Academy statistics and probability course."},
        {"title": "OpenIntro Statistics", "url": "https://www.openintro.org/book/os/", "snippet": "OpenIntro's freely available introductory statistics book."},
    ],
    "Data visualization": [
        {"title": "Matplotlib tutorials", "url": "https://matplotlib.org/stable/tutorials/index.html", "snippet": "Official Matplotlib tutorial index."},
        {"title": "Plotly getting started", "url": "https://plotly.com/python/getting-started/", "snippet": "Official Plotly Python getting started guide."},
    ],
    "Spreadsheets": [
        {"title": "Google Sheets functions", "url": "https://support.google.com/docs/answer/6000292", "snippet": "Google's list of spreadsheet functions."},
        {"title": "Excel help", "url": "https://support.microsoft.com/en-us/excel", "snippet": "Microsoft Excel documentation."},
    ],
    "Communication": [
        {"title": "Purdue OWL writing", "url": "https://owl.purdue.edu/owl/general_writing/index.html", "snippet": "Purdue Online Writing Lab guidance for clear writing."},
        {"title": "MDN writing guidelines", "url": "https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines", "snippet": "A practical standard for clear technical writing."},
    ],
    "Machine learning": [
        {"title": "scikit-learn getting started", "url": "https://scikit-learn.org/stable/getting_started.html", "snippet": "Official scikit-learn getting started guide."},
        {"title": "scikit-learn tutorial", "url": "https://scikit-learn.org/stable/tutorial/basic/tutorial.html", "snippet": "Official introductory machine learning tutorial."},
    ],
    "Pandas": [
        {"title": "pandas getting started", "url": "https://pandas.pydata.org/docs/getting_started/index.html", "snippet": "Official pandas getting started guide."},
        {"title": "pandas user guide", "url": "https://pandas.pydata.org/docs/user_guide/index.html", "snippet": "Official pandas user guide."},
    ],
    "Experimentation": [
        {"title": "Significance tests", "url": "https://www.khanacademy.org/math/statistics-probability/significance-tests-one-sample", "snippet": "Khan Academy module on significance tests."},
        {"title": "scikit-learn model selection", "url": "https://scikit-learn.org/stable/model_selection.html", "snippet": "Official documentation for evaluating and comparing models."},
    ],
    "Deep learning": [
        {"title": "PyTorch basics", "url": "https://pytorch.org/tutorials/beginner/basics/intro.html", "snippet": "Official PyTorch beginner tutorial."},
        {"title": "TensorFlow tutorials", "url": "https://www.tensorflow.org/tutorials", "snippet": "Official TensorFlow tutorial index."},
    ],
    "Linux": [
        {"title": "Ubuntu command line", "url": "https://ubuntu.com/tutorials/command-line-for-beginners", "snippet": "Ubuntu's official command line tutorial."},
        {"title": "Bash manual", "url": "https://www.gnu.org/software/bash/manual/bash.html", "snippet": "GNU Bash reference manual."},
    ],
    "CI/CD": [
        {"title": "GitHub Actions", "url": "https://docs.github.com/en/actions/learn-github-actions", "snippet": "Official GitHub Actions learning path."},
        {"title": "GitLab CI", "url": "https://docs.gitlab.com/ee/ci/", "snippet": "GitLab CI/CD documentation."},
    ],
    "Kubernetes": [
        {"title": "Kubernetes basics", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "snippet": "Official Kubernetes basics tutorial."},
        {"title": "Kubernetes concepts", "url": "https://kubernetes.io/docs/concepts/", "snippet": "Official overview of Kubernetes concepts."},
    ],
    "Cloud fundamentals": [
        {"title": "AWS getting started", "url": "https://docs.aws.amazon.com/gettingstarted/", "snippet": "Amazon Web Services getting started documentation."},
        {"title": "Microsoft Learn Azure", "url": "https://learn.microsoft.com/en-us/training/azure/", "snippet": "Microsoft's Azure training catalog."},
    ],
    "Test automation": [
        {"title": "Playwright intro", "url": "https://playwright.dev/docs/intro", "snippet": "Official Playwright introduction."},
        {"title": "pytest getting started", "url": "https://docs.pytest.org/en/stable/getting-started.html", "snippet": "Official pytest introduction, also used for automation."},
    ],
    "Problem solving": [
        {"title": "Python tutorial", "url": "https://docs.python.org/3/tutorial/", "snippet": "Use the official tutorial to practice breaking problems into code."},
        {"title": "MDN learn web development", "url": "https://developer.mozilla.org/en-US/docs/Learn", "snippet": "MDN's structured starting point for building software on the web."},
    ],
}


def normalize_skill(name: str) -> str:
    cleaned = " ".join(name.strip().lower().replace("_", " ").split())
    return ALIASES.get(cleaned, cleaned)


def normalize_role(target: str) -> tuple[str, str]:
    """Return catalog key and display title. Unknown roles use the software engineer rubric."""
    cleaned = " ".join(target.strip().lower().replace("-", " ").replace("/", " ").split())
    key = ROLE_ALIASES.get(cleaned)
    if key is None:
        for alias, mapped in ROLE_ALIASES.items():
            if alias in cleaned:
                key = mapped
                break
    if key is None:
        key = "software engineer"
    return key, CATALOG[key]["title"]
