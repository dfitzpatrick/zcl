import { Avatar, ListItem, ListItemIcon, TextField, Typography } from '@material-ui/core';
import ListSubheader from '@material-ui/core/ListSubheader';
import { useTheme } from '@material-ui/core/styles';
import useMediaQuery from '@material-ui/core/useMediaQuery';
import Autocomplete, { AutocompleteChangeDetails, AutocompleteChangeReason } from '@material-ui/lab/Autocomplete';
import axios from 'axios';
import React from 'react';
import { ListChildComponentProps, VariableSizeList } from 'react-window';

interface ProfileItem {
    id: string,
    created: string,
    name: string,
    profile_url: string,
    avatar_url: string,
}
export interface ISelectSearchOption {
    value: string,
    label: string,
    item: ProfileItem,
}
interface ISelectSearchProps  {
    freeSolo?: boolean,
    isMulti?: boolean,
    placeHolderText?: string,
    noOptionText?: string
    components?: {}
    onInputChange?:(event: object, value: string, reason: string) => void
    onChange?: (
        event: React.ChangeEvent<{}>,
        value: string|ISelectSearchOption|(string|ISelectSearchOption)[]|null,
        reason: AutocompleteChangeReason,
        details?: AutocompleteChangeDetails<any>|undefined
        ) => void

}

async function getOptions(name: string): Promise<ISelectSearchOption[]> {

    const result: ISelectSearchOption[] = []
    const url = `http://localhost:8000/api/profiles?name=${name}`
    const resp: ProfileItem[] = await (await axios.get(url)).data
    for (const item of resp) {
        result.push({label: item.name, value: item.id, item: item})
    }
    return result

}
// #region React Window For Virtualization
const LISTBOX_PADDING = 8
function renderRow(props: ListChildComponentProps) {
    const { data, index, style } = props;
    return React.cloneElement(data[index], {
      style: {
        ...style,
        top: (style.top as number) + 8,
      },
    });
  }

  const OuterElementContext = React.createContext({});

  const OuterElementType = React.forwardRef<HTMLDivElement>((props, ref) => {
    const outerProps = React.useContext(OuterElementContext);
    return <div ref={ref} {...props} {...outerProps} />;
  });
  
  function useResetCache(data: any) {
    const ref = React.useRef<VariableSizeList>(null);
    React.useEffect(() => {
      if (ref.current != null) {
        ref.current.resetAfterIndex(0, true);
      }
    }, [data]);
    return ref;
  }
  
  // Adapter for react-window
  const ListboxComponent = React.forwardRef<HTMLDivElement>(function ListboxComponent(props, ref) {
    const { children, ...other } = props;
    const itemData = React.Children.toArray(children);
    const theme = useTheme();
    const smUp = useMediaQuery(theme.breakpoints.up('sm'), { noSsr: true });
    const itemCount = itemData.length;
    const itemSize = smUp ? 36 : 48;
  
    const getChildSize = (child: React.ReactNode) => {
      if (React.isValidElement(child) && child.type === ListSubheader) {
        return 48;
      }
  
      return itemSize;
    };
  
    const getHeight = () => {
      if (itemCount > 8) {
        return 8 * itemSize;
      }
      return itemData.map(getChildSize).reduce((a, b) => a + b, 0);
    };
  
    const gridRef = useResetCache(itemCount);
  
    return (
      <div ref={ref}>
        <OuterElementContext.Provider value={other}>
          <VariableSizeList
            itemData={itemData}
            height={getHeight() + 2 * LISTBOX_PADDING}
            width="100%"
            ref={gridRef}
            outerElementType={OuterElementType}
            innerElementType="ul"
            itemSize={(index) => getChildSize(itemData[index])}
            overscanCount={5}
            itemCount={itemCount}
          >
            {renderRow}
          </VariableSizeList>
        </OuterElementContext.Provider>
      </div>
    );
  });

// #endregion

export default function SelectSearch(props: ISelectSearchProps) {
    const [option, setOption] = React.useState<ISelectSearchOption[]>([])
    React.useEffect(()=>{
        getOptions("").then((v)=>{setOption(v)})
    }, [])

    
    const itemDisplay = (option: ISelectSearchOption) => {
      return (
          <>{option.item.name}</>

      )
  }
    return (
        <div>
            <Autocomplete
                freeSolo={props.freeSolo}
                multiple={props.isMulti}       
                disableListWrap
                getOptionLabel={(o)=> {return (typeof(o) == 'string') ? o : o.label}}
                ListboxComponent={ListboxComponent as React.ComponentType<React.HTMLAttributes<HTMLElement>>}
                options={option as ISelectSearchOption[]}
                renderInput={(params) => <TextField {...params} variant="outlined" label={props.placeHolderText} />}
                renderOption={itemDisplay}
                onChange={props.onChange}
                onInputChange={props.onInputChange}
            />
        </div>
    )

}
