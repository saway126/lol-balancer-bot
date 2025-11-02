
const express = require(''express'');

const cors = require(''cors'');

const app = express();

const port = process.env.PORT || 8080;

const matches = [];

app.use(cors());

app.use(express.json());

app.options(''/saveMatch'', (req, res) => {

  res.set({

    ''Access-Control-Allow-Origin'': ''*'',

    ''Access-Control-Allow-Methods'': ''POST, OPTIONS'',

    ''Access-Control-Allow-Headers'': ''Content-Type'',

  });

  res.status(204).send();

});

app.post(''/saveMatch'', (req, res) => {

  const matchData = req.body;

  console.log(''Received match data:'', JSON.stringify(matchData, null, 2));

  matches.push(matchData);

  res.set({''Access-Control-Allow-Origin'': ''*''});

  res.status(200).json({ ok: true, stored: matchData, count: matches.length });

});

app.listen(port, () => console.log(`Server listening on port ${port}`));
