import fetchLeagues, { ILeagueResult, ISeasonResult } from '../api/leagues'

import React from 'react'
import Autocomplete, { AutocompleteChangeDetails, AutocompleteChangeReason } from '@material-ui/lab/Autocomplete'
import { TextField } from '@material-ui/core'

export interface ILeagueSelectorProps {
    onChange?: (league: ILeagueResult|null, season: ISeasonResult|null) => void
}

const seasonDropDownRef = React.createRef<React.HTMLAttributes<HTMLDivElement>>()

export default function LeagueSelector(props: ILeagueSelectorProps) {
    const [leagues, setLeagues] = React.useState<ILeagueResult[]>([])
    const [league, setLeague] = React.useState<ILeagueResult | null>(null)
    const [seasons, setSeasons] = React.useState<ISeasonResult[]>([])
    const [season, setSeason] = React.useState<ISeasonResult | null>(null)
    
    React.useEffect(() => {
        fetchLeagues().then(results => setLeagues(results))

    }, [])

    const onChangeLeague = (event: React.ChangeEvent<{}>, league: ILeagueResult | null, reason: AutocompleteChangeReason, details?: AutocompleteChangeDetails<ILeagueResult>) => {
        const divSeasons = seasonDropDownRef.current
        const leagueSeasons = (league != null) ? league.seasons : []
        setLeague(league)
        setSeasons(leagueSeasons)
    
        if (league != null) {
          setSeasons(league.seasons)
        }
        if (divSeasons != null && divSeasons.style != null) {
          divSeasons.style.display = (league == null) ? "none" : "block"
        }
        props.onChange && props.onChange(league, season)
    
      }
      const onChangeSeason = (event: React.ChangeEvent<{}>, season: ISeasonResult | null, reason: AutocompleteChangeReason, details?: AutocompleteChangeDetails<ISeasonResult>) => {
        setSeason(season)
        props.onChange && props.onChange(league, season)
      }


    return (
        <div>
            <Autocomplete
            id="league"
            options={leagues}
            getOptionLabel={(option) => option.name}
            renderInput={(params) => <TextField {...params} label="League"></TextField>}
            onChange={onChangeLeague}
          />
          <div>
            <Autocomplete
              id="season"
              ref={seasonDropDownRef}
              options={seasons}
              getOptionLabel={(option) => option.name}
              renderInput={(params) => <TextField {...params} label="Season"></TextField>}
              onChange={onChangeSeason}
              style={{ display: 'none' }}
            />
          </div>
        </div>
    )
}
