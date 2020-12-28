
import { Avatar, ListItem, ListItemAvatar } from '@material-ui/core'
import { AvatarGroup } from '@material-ui/lab'
import { isArray } from 'lodash'
import { Query } from 'material-table'
import React from 'react'
import { IProfileResult } from '../../api/profiles'
import fetchTeams, { ITeamFilters, ITeamResult } from '../../api/teams'
import { makeCSV, useFirstRender } from '../../helpers'
import FilteredTable, { IFilteredTableOptionalProps } from '../FilteredTable'
import ProfileSelector from '../ProfileSelector/ProfileSelector'
import { ISelectSearchOption } from '../SelectSearch'

const tableRef = React.createRef<any>()
type MultiSelect = string | ISelectSearchOption | (string | ISelectSearchOption)[] | null
interface ITeamTableProps extends IFilteredTableOptionalProps<ITeamResult> {
    filters?: ITeamFilters
}

export default function TeamTable(props: ITeamTableProps) {

    const firstRender = useFirstRender()
    const [players, setPlayers] = React.useState<IProfileResult[]>([])
    const filteredPlayers = (props.filters && props.filters.players && props.filters.players.split(',')) || []
    React.useEffect(()=>{
        if (!firstRender) {
            tableRef.current.onQueryChange()
        }
    }, [players])

    const dataSource = async (query: Query<ITeamResult>, sort: string) => {
        const pageState = {
            offset: query.page * query.pageSize,
            limit: query.pageSize
        }
       const filters = (firstRender && props.filters) ? props.filters : {
         players: players.map(o=>o.id).join(',')
       }
        const results = await fetchTeams({...pageState, ...filters, sort: sort})
        return results
    }
    const filterNode = () => {
        return (
          <div>
            <ProfileSelector
              isMulti
              fixedProfileIds={filteredPlayers}
              placeHolderText="Filter with Players"
              onChange={(e, value, r, d) => {
                const newValue = (isArray(value)) ? value : []
                setPlayers(newValue)
              }}
            />
            </div>
        )
    }
    const playersRender = (data: ITeamResult) => {
        const avatars = () => {
            return (
                <>  
                    <AvatarGroup>
                    {data.profiles.map((p, idx) => {
                        return <Avatar src={p.avatar_url} alt={p.name}>{p.name.charAt(0).toUpperCase()}</Avatar>
                    })}
                    </AvatarGroup>
                </>
            )
        }
        const names = makeCSV<IProfileResult>(data.profiles, ((p)=> p.name), ', ')
        return (
            <>
                    <ListItem><ListItemAvatar>{avatars()}</ListItemAvatar>
                        {names}
                    </ListItem>

                    </>
                     )
            
         
               
        

    }
    return (
        <div>
            <FilteredTable<ITeamResult>
                {...props}
                filterNodeTarget={props.filterNodeTarget}
        noFilter={props.noFilter ?? false}
        hideFilter={props.hideFilter ?? false}
        title={props.title ?? ""}
        dataSource={dataSource}
        tableRef={tableRef}
        columns={[
          {
            title: 'Id',
            field: 'id',
          
          },
          {
              title: 'Players',
              field: 'profiles',
              render: (d) => playersRender(d)
          },
          {
            title: 'Team ELO',
            field: 'team_elo',
          
          },
          {
            title: 'Total Games',
            field: 'games',
          
          },
          {
            title: 'Wins',
            field: 'wins',
          
          },
          {
            title: 'Losses',
            field: 'losses',
          
          },
          {
            title: 'Win Rate',
            field: 'win_rate',
          
          },
   
        ]}
        filterNode={filterNode()}
        options={props.options ?? {
          pageSize: 20,
          toolbar: false
        }}

      />
        </div>
    )
}
