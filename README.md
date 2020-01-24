# Deadball III MLB Roster Generator

Generate [Deadball III ("Baseball with dice")](https://wmakers.net/deadball) Rosters using the MLB API. This won't generate the lineups, but it'll give you a roster you can pull from to generate your gameday lineups. This is not an official supplement. 

## Usage

There's a pipenv file with all of the requirements. Just run `pipenv install`. Tested with Python 3.7+ currently.

	`/roster.py -t Rays --era 4.49 --dh --season 2004 > your-file-name.html`

**`-t`**

**Required.** Pass in the name of an MLB team such as "Rays" or "Yankees".

**`--season`**

Optional. If you leave this off, it'll pull the current season otherwise provide a year in YYYY format to pull the team data for that year. It is worth noting that using current stats only at the beginning of the season will almost certainly generate some overpowered pitchers whom don't have a full set of stats under their belt... so use those numbers with some caution. It can be kinda fun though if you aren't a hardcome simulationist type.

**`--era`**

Optional. Rather than use the default midpoint ERA of Deadball III, you can use an ERA midpoint you provide. It is pretty easy to look this up on something like [Baseball Reference](https://www.baseball-reference.com).

**`--dh`**

Optional. If you'd like to enable the designator hitter rules.

## Result

The resulting output is an HTML file that is formatted to printed out to paper or a PDF.