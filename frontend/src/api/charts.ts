import axios from 'axios'

export interface IChartResponse {
    feed?: any[]
    time_series?: ITimeSeriesObject[]
}
export interface ITimeSeriesObject {
    [key: string]: string|number
    id: string,
    name: string,
    game_time: string,
    total_score: number,
    minerals_floated: number,
    bunkers: number,
    tanks: number,
    depots: number,
    nukes: number,
    current_supply: number
}

export async function fetchCharts(matchId: string): Promise<IChartResponse> {
    const url = `/api/charts/${matchId}/?charts=time_series,feed`
    const result = await axios.get<IChartResponse>(url)
    return result.data
   
}   