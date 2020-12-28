import { Chip, TextField } from '@material-ui/core';
import ListSubheader from '@material-ui/core/ListSubheader';
import { useTheme } from '@material-ui/core/styles';
import useMediaQuery from '@material-ui/core/useMediaQuery';
import Autocomplete, { AutocompleteChangeDetails, AutocompleteChangeReason, AutocompleteGetTagProps, AutocompleteInputChangeReason } from '@material-ui/lab/Autocomplete';
import { isArray } from 'lodash';
import React from 'react';
import { ListChildComponentProps, VariableSizeList } from 'react-window';

export interface IAutoSelectorSelections<T> {
  item: T,
  title: string,
  disabled?: boolean
}
export interface IAutoSelectorOptionalProps<T> {
  isMulti?: boolean,
  placeHolderText?: string,
  noOptionText?: string,
  loading?: boolean
  fixedTags?: (item: T) => boolean,
  onLoadingComplete?: (selections: T | T[] | null) => void,
  onChange?: (
    event: React.ChangeEvent<{}>,
    value: T | T[] | null,
    reason: AutocompleteChangeReason,
    details?: AutocompleteChangeDetails<any> | undefined
  ) => void,
  onInputChange?: (
    event: React.ChangeEvent<{}>,
    value: string,
    reason: AutocompleteInputChangeReason
  ) => void

}
interface IAutoSelectorProps<T> extends IAutoSelectorOptionalProps<T> {
  data: T[],

  getOptionLabel: (item: T) => string,
  initialSelections?: () => IAutoSelectorSelections<T>[],
  renderItem: (item: T) => React.ReactNode,



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



export default function AutoSelector<T>(props: IAutoSelectorProps<T>) {

  const fixedTagsPredicate = props.fixedTags ?? ((item: T) => false)
  const fixedTags = (props.fixedTags === undefined || !props.isMulti) ? null : props.data.filter(fixedTagsPredicate)

  const [selections, setSelections] = React.useState<T | T[] | null>(fixedTags)

  React.useEffect(() => {
    if (props.isMulti) {
      const fixedSelections = props.data.filter(fixedTagsPredicate)
      setSelections(fixedSelections)
      props.onLoadingComplete && props.onLoadingComplete(fixedSelections)
    }
  }, [props.loading])

  const renderTagsDefault = (tagValue: T[], getTagProps: AutocompleteGetTagProps) => {
    if (props.isMulti) {
      return (
        tagValue.map((option, index) => {
          return (
            <Chip
              label={props.getOptionLabel(option)}
              {...getTagProps({ index })}
              disabled={props.fixedTags && props.fixedTags(option)}
            />
          )
        })
      )
    }
  }
  return (
    <div>
      <Autocomplete
        loading={props.loading}
        freeSolo={false}
        multiple={props.isMulti}
        value={selections}
        disableListWrap
        ListboxComponent={ListboxComponent as React.ComponentType<React.HTMLAttributes<HTMLElement>>}
        options={props.data}
        renderInput={(params) => <TextField {...params} variant="outlined" label={props.placeHolderText} />}
        renderOption={props.renderItem}
        onChange={(e, v, r, d) => {
          const value = (isArray(v) && isArray(fixedTags)) ? fixedTags.concat(v.filter(o => !fixedTagsPredicate(o))) : v
          setSelections(value)
          props.onChange && props.onChange(e, value, r, d)
        }}
        getOptionLabel={props.getOptionLabel}
        renderTags={renderTagsDefault}
        onInputChange={props.onInputChange}



      />
    </div>
  )
}
