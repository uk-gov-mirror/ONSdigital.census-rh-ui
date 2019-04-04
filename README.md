[![Codacy Badge](https://api.codacy.com/project/badge/Grade/f86365f13b044491b9047a549589109f)](https://www.codacy.com/app/philwhiles/census-rh-ui?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/census-rh-ui&amp;utm_campaign=Badge_Grade)
[![Build Status](https://travis-ci.org/ONSdigital/census-rh-ui.svg?branch=master)](https://travis-ci.org/ONSdigital/census-rh-ui)
[![codecov](https://codecov.io/gh/ONSdigital/census-rh-ui/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/census-rh-ui)

# Respondent Home Python Web Application
Respondent Home is part of ONS's Census Survey Data Collection platform. It allows users to validate their Internet Access Code (IAC) and forwards
them to the [ONS eQ Survey Runner](https://github.com/ONSdigital/eq-survey-runner) upon successful validation.

![The ONS Survey Data Collection platform](/images/sdc_platform.png?raw=true)

This repository contains the Python [AIOHTTP](http://docs.aiohttp.org/en/stable/) application that is the user interface for the Respondent Home product.

## Payload

The fields required to launch an eQ survey are documented in the [ons-schema-definitions](http://ons-schema-definitions.readthedocs.io/en/latest/respondent_management_to_electronic_questionnaire.html#required-fields).


## Installation
Install the required Python packages for running and testing Respondent Home within a virtual environment:

  `make install`

## Running
To run this application in development use:

  `make run`

and access using [http://localhost:9092](http://localhost:9092).

## Tests
To run the unit tests for Respondent Home:

  `make test`

To bring up all the RAS/RM & eQ Runner services and run the integration tests against them and Respondent Home:

  `make local_test`

NB: Waiting for the services to be ready will likely take up to ten minutes.


## Docker
Respondent Home is one part of the RAS/RM docker containers:

  [https://github.com/ONSdigital/ras-rm-docker-dev](https://github.com/ONSdigital/ras-rm-docker-dev)


## Environment Variables
The environment variables below must be provided:

```
JSON_SECRET_KEYS
SECRET_KEY
```

## Internationalisation

We use flask-babel to do internationalisation.  To extract messages from source, in the project root run the following command.

```
pipenv run pybabel extract -F babel.cfg -o app/translations/messages.pot .
```

This will extract messages and place them in the translations/messages.pot file ready for translation.

You should only need to create the language files once.

To create Welsh language files, run the following command

```
pipenv run pybabel init -i app/translations/messages.pot -d app/translations -l cy
```

To create the gaelic language files, use the following:

```
pipenv run pybabel init -i app/translations/messages.pot -d app/translations -l gd
```

### Getting text translated

Our current language translation service requires a .csv rather than a .po file. To convert a .po file to a .csv you'll need to install the Python translate-toolkit:
```
brew install translate-toolkit
```

To generate the .csv file:
```
po2csv app/translations/cy/LC_MESSAGES/messages.po app/translations/static-cy.csv
```

To convert back to a .po file:
```
csv2po app/translations/static-cy.csv app/translations/cy/LC_MESSAGES/messages.po
```

*Important:* There are some encoding issues when opening the .csv file in Excel. Opening in Google sheets and saving as a .xslx file resolves this.

### Compiling the translations

To compile the language files for use in the application, use the following:

```
pipenv run pybabel compile -d app/translations
```

As strings are added to the application, you will need to update but not overwrite the translations for the various languages.
To update the language strings, use:

```
pipenv run pybabel update -i app/translations/messages.pot -d app/translations
```
