import { Avatar, createStyles, ListItem, ListItemAvatar, makeStyles, TextField, Theme } from '@material-ui/core'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { debounce } from 'lodash'
import { Query } from 'material-table'
import React from 'react'
import { fetchLeaderboards, ILeaderboardFilters, ILeaderboardResult } from '../../api/leaderboard'
import { goodTimeDiff, useFirstRender } from '../../helpers'
import FilteredTable, { IFilteredTableOptionalProps } from '../FilteredTable'
import MarginContainer from '../MarginContainer/MarginContainer'
import SelectSearch from '../SelectSearch'

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

interface ILeaderboardProps extends IFilteredTableOptionalProps<ILeaderboardResult> {
  filters?: ILeaderboardFilters
}
const tableRef = React.createRef<any>()
export default function Leaderboard(props: ILeaderboardProps) {
  const classes = useStyles()
  const firstRender = useFirstRender()
  const [mode, setMode] = React.useState("2v2v2v2")
  const [search, setSearch] = React.useState("")


  React.useEffect(() => {
    if (!firstRender) {
      tableRef.current.onQueryChange()
    }
  }, [search, mode])

  const onInputChange = debounce(
    (e: object, v: string, r: string) => {
      setSearch(v)
    }, 1000)
  
  const dataSource = async (query: Query<ILeaderboardResult>, sort: string) => {
    const pageState = {
      offset: query.page * query.pageSize,
      limit: query.pageSize
  }
  const filters = (firstRender && props.filters) ? props.filters : {
      name: search,
      mode: mode,
    }
  const results = await fetchLeaderboards({ ...pageState, ...filters, sort: sort })
  return results

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


  const filterNode = () => {
    return (
      <div className={classes.filters}>
        <Autocomplete
          id="mode"
          options={['2v2v2v2', '1v1', '3v3v3v3']}
          defaultValue="2v2v2v2"
          renderInput={(params) => <TextField {...params} label="Mode"></TextField>}
          onChange={(e,v) => setMode(v == null? "" : v)}
          />
        <SelectSearch
              freeSolo
              noOptionText="Start typing to search for players"
              placeHolderText="Find Player"
              onInputChange={onInputChange}
             />
   
      </div>

    )
  }
  const onRowClickDefault =  (
    event?: React.MouseEvent<Element, MouseEvent>|undefined,
    rowData?: ILeaderboardResult | undefined,
    toggleDetailPanel?: ((panelIndex?: number | undefined) => void)|undefined
    ) => {
      if (rowData) {window.location.href = `/profiles/${rowData.profile.id}`}
      
    }
  return (
    <MarginContainer>
      <FilteredTable<ILeaderboardResult>
       
        noFilter={props.noFilter ?? false}
        hideFilter={props.hideFilter ?? false}
        title={props.title ?? ""}
        {...props}
        dataSource={dataSource}
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
          { title: 'ELO', field: 'elo', render: d=>parseFloat(d.elo).toFixed(0) },
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
        onRowClick={onRowClickDefault}
        filterNode={filterNode()}
        options={props.options ?? {
          pageSize: 20,
          toolbar: false
        }}

      />
    </MarginContainer>
  )
}
