import { Avatar, createStyles, ListItem, ListItemAvatar, makeStyles, Theme, Typography } from '@material-ui/core'
import { Column, Query } from 'material-table'
import React from 'react'
import { ILeagueResult, ISeasonResult } from '../../api/leagues'
import fetchStandings, { IStandingFilters, IStandingResult } from '../../api/standings'
import { useFirstRender } from '../../helpers'
import FilteredTable, { IFilteredTableOptionalProps } from '../FilteredTable'
import LeagueSelector from '../LeagueSelector'
import MarginContainer from '../MarginContainer/MarginContainer'

const tableRef = React.createRef<any>()

interface ILeagueTableProps extends IFilteredTableOptionalProps<IStandingResult> {
    filters?: IStandingFilters

}

export default function LeagueTable(props: ILeagueTableProps) {
    const title = props.title ?? ""
    const firstRender = useFirstRender()
    const [league, setLeague] = React.useState<ILeagueResult | null>(null)
    const [season, setSeason] = React.useState<ISeasonResult | null>(null)

    React.useEffect(() => {
        if (!firstRender) {
            tableRef.current.onQueryChange()
          }
    }, [season, league])
    const filterNode = () => {
        return (
            <div>
                <LeagueSelector
                    onChange={(l, s) => {
                        setLeague(l)
                        setSeason(s)
                    }}
                />
            </div>
        )
    }
    const dataSource = async (query: Query<IStandingResult>, sort: string) => {
        const pageState = {
            offset: query.page * query.pageSize,
            limit: query.pageSize
        }
        const filters = (firstRender && props.filters) ? props.filters : {
            league: league ? league.id.toString() : "",
            season: season ? season.id.toString() : "",
        
          }
        const results = await fetchStandings({ ...pageState, ...filters, sort: sort })
        return results

    }
    const name = (d: IStandingResult) => {
        return (    
            <>
                <ListItem>
                    <ListItemAvatar><Avatar src={d.avatar_url}>{d.name}</Avatar></ListItemAvatar>
                    <Typography>{d.name}</Typography>
                </ListItem>
            </>
        )
    }
    const columns: Column<IStandingResult>[] = [
        { title: 'Rank', field: 'rank' },
        {
            title: 'Player',
            field: 'name',
            render: d => name(d)
        },
        {
            title: 'ADJ W/R %',
            field: 'adjusted_win_rate',
            render: d => parseFloat(d.adjusted_win_rate.toFixed(2))
        },
        { title: 'Games', field: 'total_matches' },
        { title: 'W', field: 'total_wins' },
        { title: 'L', field: 'total_losses' },
        { title: 'D', field: 'total_draws' },
        {
            title: 'Act W/R %',
            field: 'win_rate',
            render: d => parseFloat(d.win_rate.toFixed(2))
        },
        {
            title: 'W/R MOD',
            field: 'rate',
            render: d => d.rate.toFixed(2)
        },

    ]
    const onRowClickDefault =  (
        event?: React.MouseEvent<Element, MouseEvent>|undefined,
        rowData?: IStandingResult | undefined,
        toggleDetailPanel?: ((panelIndex?: number | undefined) => void)|undefined
        ) => {
          if (rowData) {window.location.href = `/profiles/${rowData.id}`}
          
        }
    return (
        <MarginContainer>
            <FilteredTable<IStandingResult>
                {...props}
                noFilter={props.noFilter ?? false}
                hideFilter={props.hideFilter ?? false}
                title={title}
                dataSource={dataSource}
                tableRef={tableRef}
                columns={columns}
                filterNode={filterNode()}
                options={props.options ?? {
                    pageSize: 20,
                    toolbar: false
                }}
                onRowClick={onRowClickDefault}

            />
        </MarginContainer>
    )
}
