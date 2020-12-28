
import { Avatar, ListItem, ListItemAvatar, ListItemText } from '@material-ui/core'
import { AutocompleteChangeReason, AutocompleteInputChangeReason } from '@material-ui/lab'
import { debounce, isArray } from 'lodash'
import React from 'react'
import fetchProfiles, { IProfileResult } from '../../api/profiles'
import AutoSelector, { IAutoSelectorOptionalProps } from '../AutoSelector/AutoSelector'
import { useFirstRender } from '../../helpers'
interface IProfileSelectorProps extends IAutoSelectorOptionalProps<IProfileResult> {
    fixedProfileIds?: string[],
    placeHolderText?: string
}
type IProfileSelectorType = IProfileResult|IProfileResult[]|null
export default function ProfileSelector(props: IProfileSelectorProps) {
    const firstRender = useFirstRender()
    const fixedProfiles = props.fixedProfileIds ?? []
    const [search, setSearch] = React.useState("")
    const fixedProfilePredicate = (item: IProfileResult) => {return fixedProfiles.includes(item.id)}
    const [data, setData] = React.useState<IProfileResult[]>([])
    const [selection, setSelection] = React.useState<IProfileSelectorType>(null)
    const [loading, setLoading] = React.useState(false)
    React.useEffect(()=>{
        if (!firstRender) {
            setLoading(true)
            fetchProfiles({
                limit: 10000,
                offset: 0,
                name: search
            })?.then(ps=> {
                if (!isArray(ps)) {
                    setData(ps.results)
                }
                setLoading(false)
            })
        }
       
    }, [search])
 
   
    const onInputChange = debounce(
        (
        event: React.ChangeEvent<{}>,
        value: string,
        reason: AutocompleteInputChangeReason
      ) => {
          setSearch(value)
      }, 500)
    const renderItem = (item: IProfileResult) => {
        return (
            <div>
            <ListItem>
                <ListItemAvatar>
                    <Avatar src={item.avatar_url} alt={item.name}>{item.name.charAt(0)}</Avatar>
                </ListItemAvatar>
                <ListItemText primary={item.name}

                />
                
                
            </ListItem>
            </div>
        )
    }
    return (
        <div>
            <AutoSelector<IProfileResult>
                data={data}
     
                loading={loading}
                isMulti={props.isMulti}
                renderItem={renderItem}
                getOptionLabel={(item) => item.name}
                fixedTags={fixedProfilePredicate}
                onChange={(e,v,r,d)=> {
                    setSelection(v)
                    props.onChange && props.onChange(e,v,r,d)
                }}
                onLoadingComplete={(selections)=>setSelection(selections)}
                placeHolderText={props.placeHolderText}
                onInputChange={onInputChange}



            />
        </div>
    )
}
