import React from 'react'
import { components, createFilter, ValueType } from 'react-select'
import AsyncSelect from 'react-select/async';
import axios from 'axios'
import { Avatar, ListItem, ListItemIcon } from '@material-ui/core'
import SearchIcon from '@material-ui/icons/Search';


type LeaderboardItem = {
    id: number,
    mode: string,
    name: string,
    rank: number,
    created: string,
    updated: string,
    games: number,
    wins: number,
    losses: number,
    elo: string,
    win_rate: string,
    profile: {
        id: string,
        created: string,
        name: string,
        profile_url: string,
        avatar_url: string,
        discord_users: string[]
    }
}
type ProfileItem = {
    id: string,
    created: string,
    name: string,
    profile_url: string,
    avatar_url: string,
}
type OptionType = {
    value: string,
    label: string,
    item: ProfileItem,
}


async function getOptions(name: string): Promise<OptionType[]> {
    if (name.length < 2) { return [] }
    const result: OptionType[] = []
    const url = `http://localhost:8000/api/profiles?name=${name}`
    const resp: ProfileItem[] = await (await axios.get(url)).data
    for (const item of resp) {
        result.push({label: item.name, value: item.id, item: item})
    }
 
    return result

}

export default function MultiSelectPlayer() {
    
    const Option = (props: any) => {
        const item = props.data.item
        return (
            <>
            <ListItem button>
                <ListItemIcon>
                    <Avatar src={item.avatar_url} />
                </ListItemIcon>
            

            <components.Option {...props} />
            </ListItem>
            </>
        )
      }
    const NoOptionsMessage = (props: any) => {
        const myProps = {
            ...props,
            children: "Start typing to search for players"
        }
   
        return (
            <components.NoOptionsMessage {...myProps} />
        )
    }
    const DropdownIndicator = (
        props: any
      ) => {
        return (
          <components.DropdownIndicator {...props}>
            <SearchIcon />
          </components.DropdownIndicator>
        )
      }
    const Placeholder = (props:any) => {
        const myProps = {
            ...props,
            children: "Search Players"
        }
        return <components.Placeholder {...myProps} />;
    };
    
    const handleInputChange = (value: string) => {
        setName(value)
    }
    const loadOptions = (name: string) => {
        return getOptions(name)
    }
    
    const [selectedOption, setSelectedOption] = React.useState<ValueType<OptionType>>(null)
    const [name, setName] = React.useState("")
    const [options, setOptions] = React.useState<OptionType[]>([])
    React.useEffect(() => {
        getOptions(name).then((resp: any) => {
            setOptions(resp)
        })
    }, [])

    return (
        <div>
            <AsyncSelect
                cacheOptions
                defaultOptions
                isMulti
                defaultValue={selectedOption}
                onChange={(value) => { setSelectedOption(value)}}
                onInputChange={handleInputChange}
                loadOptions={loadOptions}
                filterOption={createFilter({ignoreAccents: false})}
                components={{Option, NoOptionsMessage, DropdownIndicator, Placeholder}}
                
            />
        </div>
    )
}
