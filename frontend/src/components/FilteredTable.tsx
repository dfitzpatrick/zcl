import { Card, CardHeader, Grid, IconButton, makeStyles } from '@material-ui/core'
import FilterListIcon from '@material-ui/icons/FilterList'
import MaterialTable, { Column, Options, Query, QueryResult } from 'material-table'
import React from 'react'
import { useFirstRender } from '../helpers'
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
export interface IFilteredTableOptionalProps<T extends object> {
  noFilter?: boolean,
  hideFilter?: boolean,
  title?: string,
  options?: Options<T>,
  filterNodeTarget?: string,
  gridItemParams?: {}
  gridFilterParams?: {}
  onRowClick?: (event?: React.MouseEvent<Element, MouseEvent>|undefined,
    rowData?: T | undefined,
    toggleDetailPanel?: ((panelIndex?: number | undefined) => void)|undefined) => void
}
export interface IFilteredTableProps<T extends object> extends IFilteredTableOptionalProps<T> {
  dataSource: (query: Query<T>, sort: string) => Promise<ILimitedQuery<T>>,
  tableRef: React.RefObject<any>
  columns: Column<T>[],
  filterNode: React.ReactNode

  onOrderChange?: (colId: number, direction: "desc" | "asc") => void

}
export interface ILimitedQuery<T> {
  count: number,
  next: string,
  previous: string,
  results: T[]
}

export default function FilteredTable<T extends object>(props: IFilteredTableProps<T>) {
  const filterRef = React.createRef<HTMLDivElement>()
  const tableRef = props.tableRef
  const classes = useStyles()
  const noFilter = props.noFilter ?? false
  const [filterVisible, setFilterVisible] = React.useState(!props.hideFilter ?? true)
  const title = props.title ?? ""
  const firstRender = useFirstRender()

  const [loading, setLoading] = React.useState(true)
  const [page, setPage] = React.useState(0)
  const [pageSize, setPageSize] = React.useState(0)


  React.useEffect(() => {
    const filters = filterRef.current
    if ((!firstRender) && (tableRef && tableRef.current != null)) {
      tableRef.current.onQueryChange()
    } else {
      if (props.filterNodeTarget != undefined) {
        //ReactDOM.render(<React.Fragment>{filterNode()}</React.Fragment>, document.getElementById(props.filterNodeTarget))
      }
    }
    if (filters && filters.style) {
      filters.style.display = (!noFilter && filterVisible) ? "block" : "none"
    }
  }, [])
  const toggleFilters = (event: any) => {
    const filters = filterRef.current
    setFilterVisible(!filterVisible)
    if (filters && filters.style) {
      filters.style.display = !filterVisible ? "block" : "none"
    }

  }

  const filterButton = () => {
    if (!noFilter) {
      return (
        <IconButton
          id="btnFilters"
          onClick={(e) => toggleFilters(e)}
        >
          <FilterListIcon />
        </IconButton>
      )
    }
    return ""
  }
  const filterNode = () => {
    return (
      <>

        <Card>
          <CardHeader

            title={title}
            action={filterButton()}
          />
          <div ref={filterRef} className={classes.filters}>
            {props.filterNode}
          </div>
        </Card>

      </>

    )
  }
  const remoteData = (query: Query<T>): Promise<QueryResult<T>> => {
    const sort = () => {
      if (query.orderBy && query.orderBy.field) {
        const pfx = query.orderDirection == "asc" ? "" : "-"
        return pfx + query.orderBy.field
      }
      return ""
    }
    return new Promise((resolve, reject) => {
      const queryPage = query != null ? query.page : page
      const queryPageSize = query != null ? query.pageSize : pageSize

      setLoading(true)
      props.dataSource(query, sort()).then(data => {
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


  return (
    <div>
      <Grid container>


        <Grid item xs={12} {...props.gridFilterParams} style={{padding: '10px'}}>
          <Card>
            <CardHeader
              title={title}
              action={filterButton()}
            />
            <div ref={filterRef} className={classes.filters}>
              {props.filterNode}
            </div>

          </Card>
        </Grid>
        <Grid item  xs={12} {...props.gridItemParams}>

          <MaterialTable
            onOrderChange={(c, d) => props.onOrderChange && props.onOrderChange(c, d)}
            options={props.options ?? {}}
            tableRef={props.tableRef}
            columns={props.columns}
            isLoading={loading}
            data={remoteData}
            onRowClick={props.onRowClick}

          />
        </Grid>
      </Grid>
    </div>

  )
}
