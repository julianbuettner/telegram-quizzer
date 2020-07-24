# Telegram Quizzer

Learn something in an index card style
with the help of telegram.

## Requirements
```bash
python3 -m pip install -r requirements.txt
```

## Start
```python
./start.sh
```

## Config
```ini
[config]
bottoken = get it from the telegram botfather

# Message to be sent for /start
welcome = Welcome!
    Here you can learn question catalogues.

[catalogues]
# See https://github.com/RandomApfel/questioncataloguing
# for how to create and dump a catalogue

# command = patch.json:mediadir:description
# command = patch.json::description 

```

## Usage
1. Install the requirements
2. Create one or more catalogues and dump them to json text files
Take a look at https://github.com/RandomApfel/questioncataloguing
to learn how to do that.  

3. Create a config entry within the `[catalogues]` section.
If you want to start the questioning with the Telegram
command `/vocabulary` and your catalogue dump is at
`./catalogues/vocabulary.json` then your entry should look like:

```ini
[catalogues]
vocuabulary = ./catalogues/vocabulary.json::Get asked about vocabulary
```

It will now be shown when sending `/help` in Telegram.

