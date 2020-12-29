import { Avatar, FormControlLabel, TextField, makeStyles, createStyles, Theme } from '@material-ui/core'
import Checkbox from '@material-ui/core/Checkbox'
import { isArray } from 'lodash'
import { Query } from 'material-table'
import moment from 'moment'
import React from 'react'
import { ILeagueResult, ISeasonResult } from '../../api/leagues'
import fetchMatches, { IMatchFilters, IMatchResult } from '../../api/matches'
import { IProfileResult } from '../../api/teams'
import { useFirstRender } from '../../helpers'
import FilteredTable, { IFilteredTableOptionalProps } from '../FilteredTable'
import LeagueSelector from '../LeagueSelector'
import ProfileSelector from '../ProfileSelector/ProfileSelector'
import TankIcon from '../../assets/img/unitIcons/tank.png'
import TurretIcon from '../../assets/img/unitIcons/turret.png'
import TimerIcon from '@material-ui/icons/Timer'
import MarginContainer from '../MarginContainer/MarginContainer'
import MidIcon from '../../assets/img/unitIcons/ghost.png'
import BunkerIcon from '../../assets/img/unitIcons/bunker.png'
import SCVIcon from '../../assets/img/unitIcons/scv.png'
import SupplyDepotIcon from '../../assets/img/unitIcons/supplydepot.png'
interface IMatchProps extends IFilteredTableOptionalProps<IMatchResult> {
  filters?: IMatchFilters
}
const useStyles = makeStyles((theme: Theme) => createStyles({
  filters: {
    '& > *': {
      margin: '10px',
    },
    '& last-child': {
      marginBottom: 0,
      backgroundColor: 'red',
    }
  }
}))
const tableRef = React.createRef<any>()

export default function MatchTable(props: IMatchProps) {
  const classes = useStyles()
  const today = new Date().toISOString().split('T')[0] //yyyy-mm-dd
  const firstRender = useFirstRender()
  const filteredPlayers = (props.filters && props.filters.players && props.filters.players.split(',')) || []
  const [beginDate, setBeginDate] = React.useState("")
  const [endDate, setEndDate] = React.useState("")
  const [winners, setWinners] = React.useState<IProfileResult[]>([])
  const [players, setPlayers] = React.useState<IProfileResult[]>([])
  const [league, setLeague] = React.useState<ILeagueResult | null>(null)
  const [season, setSeason] = React.useState<ISeasonResult | null>(null)
  const [ranked, setRanked] = React.useState(false)

  React.useEffect(() => {
    if (!firstRender) {
      tableRef.current.onQueryChange()
    }
  }, [beginDate, endDate, winners, players, league, season, ranked])

  const dataSource = async (query: Query<IMatchResult>, sort: string) => {
    const pageState = {
      offset: query.page * query.pageSize,
      limit: query.pageSize
  }
  const filters = (firstRender && props.filters) ? props.filters : {
    players: players.map(o=>o.id).join(','),
    winners: winners.map(o=>o.id).join(','),
    league: league ? league.id.toString() : "",
    season: season ? season.id.toString() : "",
    ranked: ranked ? "1" : "0",
    before_date: beginDate,
    after_date: endDate,


  }
    const results = await fetchMatches({...pageState,  ...filters, sort: sort })
    return results

  }
  const onRowClickDefault =  (
    event?: React.MouseEvent<Element, MouseEvent>|undefined,
    rowData?: IMatchResult | undefined,
    toggleDetailPanel?: ((panelIndex?: number | undefined) => void)|undefined
    ) => {
      if (rowData) {window.location.href = `/matches/${rowData.id}`}
      
    }
  const filterNode = () => {
    return (
      <div className={classes.filters}>
        <ProfileSelector
          isMulti
          fixedProfileIds={filteredPlayers}
          placeHolderText="Filter with Players"
          onChange={(e, value, r, d) => {
            const newValue = (isArray(value)) ? value : []
            setPlayers(newValue)
          }}

        />

        <ProfileSelector
          isMulti
          placeHolderText="Filter Winners"
          onChange={(e, value, r, d) => {
            const newValue = (isArray(value)) ? value : []
            setWinners(newValue)
          }}


        />

        <div>
          <TextField
            id="date"
            label="Start"
            type="date"
            defaultValue={endDate}
            onChange={(elem) => { setEndDate(elem.target.value) }}
            InputLabelProps={{
              shrink: true,
            }}
          />
          <TextField
            id="date"
            label="End"
            type="date"
            defaultValue={beginDate}
            onChange={(elem) => { setBeginDate(elem.target.value) }}
            InputLabelProps={{
              shrink: true,
            }}
          />

        </div>
        <LeagueSelector
          onChange={(l, s) => {
            setLeague(l)
            setSeason(s)
          }}
        />
        <FormControlLabel
          control={
            <Checkbox
              name="checkedB"
              color="secondary"
              value={ranked}
              onClick={(e)=>setRanked(!ranked)}
              
            />
          }
          label="Ranked"
        />

      </div>
    )
  }

  return (
    <MarginContainer>
      <FilteredTable<IMatchResult>
        {...props}
        noFilter={props.noFilter ?? false}
        hideFilter={props.hideFilter ?? false}
        title={props.title ?? ""}
        dataSource={dataSource}
        onRowClick={onRowClickDefault}
        tableRef={tableRef}
        columns={[
          {
            title: 'Date',
            field: 'match_date',
            render: data => moment(data.match_date).format("lll"),
          },
          { title: 'Players', field: 'names', sorting: false },
          { title: 'Winners', field: 'alt_winners', sorting: false },
          { title: 'ELO Avg', field: 'elo_average' },
          { title: <TimerIcon />, field: 'game_length', render: d=> d ? moment.utc(d.game_length * 1000).format('HH:mm:ss') : "Unknown" },
        
          { title: <Avatar alt="mid" src={MidIcon} />, field: 'mid', render: d=>d.mid ? (d.mid == true ? "Yes" : "No") : 'No' },
          { title: 'Nukes', field: 'nukes', render: d=>d.nukes ? d.nukes : '0' },
          { title: <Avatar alt="bunkers" src={BunkerIcon} />, field: 'bunkers', render: d=>d.bunkers ? d.bunkers : '0' },
          { title: <Avatar alt="Supply Depots" src={SupplyDepotIcon} />, field: 'supply_depots', render: d=>d.supply_depots ? d.supply_depots : '0' },
          { title: <Avatar alt="Tanks" src={TankIcon} />, field: 'tanks', render: d=> d.tanks ? d.tanks : '0'},
          { title: <Avatar src={TurretIcon} />, field: 'turrets', render: d=> d.turrets ? d.turrets : '0' }
        ]}
        filterNode={filterNode()}
        options={props.options ?? {
          pageSize: 20,
          toolbar: false
        }}

      />
    </MarginContainer>
  )
}
