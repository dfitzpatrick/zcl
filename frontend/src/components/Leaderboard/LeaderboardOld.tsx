import { Avatar, Card, CardHeader, IconButton, ListItem, ListItemAvatar, TextField, Typography } from '@material-ui/core'
import MaterialTable, { Query, QueryResult } from 'material-table'
import React from 'react'
import fetchLeaderboard, { ILeaderboardResult, ILeaderboardFilters } from '../../api/leaderboard'
import { goodTimeDiff, useFirstRender } from '../../helpers'
import { debounce } from 'lodash'
import { makeStyles } from '@material-ui/core/styles'
import FilterListIcon from '@material-ui/icons/FilterList'
import Autocomplete from '@material-ui/lab/Autocomplete'
import SelectSearch from '../SelectSearch'
import LeagueSelector from '../LeagueSelector'
import { ILeagueResult, ISeasonResult } from '../../api/leagues'

const useStyles = makeStyles({
  filters: {
    '& > *': {
      margin: '10px',
    },
    '& last-child': {
      marginBottom: 0,
      backgroundColor: 'red',
    },
  },

})

const tableRef = React.createRef<any>()
const filterRef = React.createRef<HTMLDivElement>()
export default function Leaderboard() {
  const classes = useStyles()
  const firstRender = useFirstRender()
  const [loading, setLoading] = React.useState(true)
  const [leaderboards, setLeaderboards] = React.useState<ILeaderboardResult[]>([])
  const [page, setPage] = React.useState(0)
  const [pageSize, setPageSize] = React.useState(20)
  const [mode, setMode] = React.useState("2v2v2v2")
  const [search, setSearch] = React.useState("")
  const [league, setLeague] = React.useState<ILeagueResult|null>(null)
  const [season, setSeason] = React.useState<ISeasonResult|null>(null)

  React.useEffect(() => {
    if (!firstRender) {
      tableRef.current.onQueryChange()
    }
  }, [search])
 
const onInputChange = debounce(
  (e: object, v: string, r: string) => {
    setSearch(v)
  }, 1000)

  

  
  const remoteData = (query: Query<ILeaderboardResult> | null): Promise<QueryResult<ILeaderboardResult>> => {
    return new Promise((resolve, reject) => {
      const queryPage = query != null ? query.page : page
      const queryPageSize = query != null ? query.pageSize : pageSize
      const cfg: ILeaderboardFilters = {
        mode: mode,
        limit: queryPageSize,
        offset: queryPage * queryPageSize,
        name: search
      }
      setLoading(true)
      fetchLeaderboard(cfg).then(data => {
        setLeaderboards(data.results)
        setLoading(false)
        setPage(queryPage)
        setPageSize(queryPageSize)

        resolve({
          data: data.results,
          totalCount: data.count,
          page: queryPage
        })
      })
    })
  }

const nameBadge = (o: ILeaderboardResult) => {
  return (
    <ListItem>
      <ListItemAvatar>
        <Avatar src={o.profile.avatar_url}>{o.profile.name}</Avatar>

      </ListItemAvatar>
      {o.profile.name}
    </ListItem>
    
  )
}


const filterButton = () => {

  if (true) {
    return (
      <IconButton
        id="btnFilters"
        
      >
        <FilterListIcon />
      </IconButton>
    )
  }
  return ""
}
const onLeagueSeasonChange = (league: ILeagueResult|null, season: ISeasonResult|null) => {
}
  return (
    <>
    <Card className={classes.filters}>
      <CardHeader
        title="Public Leaderboard"
        action={filterButton()}
      />
    
      <div ref={filterRef} className={classes.filters}>
        <Autocomplete
          id="mode"
          options={['2v2v2v2', '1v1']}
          defaultValue="2v2v2v2"
          renderInput={(params) => <TextField {...params} label="Mode"></TextField>}
          />
        <SelectSearch
              freeSolo
              noOptionText="Start typing to search for players"
              placeHolderText="Find Player"
              onInputChange={onInputChange}
             />
        <LeagueSelector
          onChange={(l, s) => {
            setLeague(l)
            setSeason(s)
          }}
        />

    
      </div>



    </Card>
    <MaterialTable
      tableRef={tableRef}
      columns={[
        {
          title: 'Rank', field: 'rank',
        },
        { 
          title: 'Name', 
          field: 'name',
          render: o => nameBadge(o)
         },
        { title: 'ELO', field: 'elo' },
        { title: 'Win %', field: 'win_rate' },
        { title: 'W', field: 'wins' },
        { title: 'L', field: 'losses' },
        { 
          title: 'Updated', 
          field: 'updated',
          render: o => goodTimeDiff({
            to: o.updated,
            suffix: "ago"
          })
        },

      ]}
      data={(query: Query<ILeaderboardResult>) => {
        return remoteData(query)
      }}
      isLoading={loading}
      options={{
        toolbar: false,
        pageSize: pageSize
      }}
      />
      </>
    )
}


