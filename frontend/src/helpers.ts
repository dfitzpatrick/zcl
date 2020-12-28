import {isArray} from 'lodash'
import React from 'react'

export function makeCSV<T>(obj: T|T[], accessor: (obj: T) => string, delim: string = ',') {
    var result = ""
 
    if (isArray(obj)) {
        obj.forEach((v) => { result += accessor(v) + delim })
        result = result.slice(0, -1)
    } else {
        result += accessor(obj)
    }

    return result
}

export function parseSimpleQuerystring(queryString: string) {
    var query: any = {};
    var pairs = (queryString[0] === '?' ? queryString.substr(1) : queryString).split('&');
    for (var i = 0; i < pairs.length; i++) {
        var pair = pairs[i].split('=');
        query[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
    }
    return query;
}
export function useFirstRender() {
    const firstRender = React.useRef(true)
    React.useEffect(() => {
      firstRender.current = false
    }, [])
    return firstRender.current
  }

  interface IGoodTimeDiffSettings {
    from?: string,
    to?: string,
    prefix?: string,
    suffix?: string
  }
  export function goodTimeDiff(settings: IGoodTimeDiffSettings) {
    // https://github.com/gayanSandamal/good-time
    // Doesn't appear to be on npm
    let now = new Date()
    let start: any = (settings.from !== undefined) ? new Date(settings.from) : now
    let end: any = (settings.to !== undefined) ? new Date(settings.to) : undefined
    let diff

    // check for prefixes and suffixes
    let prefix = (settings.prefix !== undefined) ? settings.prefix : undefined
    let suffix = (settings.suffix !== undefined) ? settings.suffix : undefined

    let timeDiff = Math.abs(start - end)
    let diffSeconds = Math.ceil(timeDiff / (1000))
    let diffMinutes = Math.ceil(timeDiff / (1000 * 60))
    let diffHours = Math.ceil(timeDiff / (1000 * 3600))
    let diffDays = Math.ceil(timeDiff / (1000 * 3600 * 24))
    if (diffSeconds < 60) {
        diff = diffSeconds < 10 ? ' Just Now' : diffSeconds + ' seconds'
        if (prefix !== undefined) {
            diff = prefix + ' ' + diff
        }
        if (suffix !== undefined && diffSeconds > 10) {
            diff = diff + ' ' + suffix
        }
    } else if (diffSeconds < (60 * 60)) {
        diff = diffMinutes > 1 ? diffMinutes + ' minutes' : diffMinutes + ' minute'
        if (prefix !== undefined) {
            diff = prefix + ' ' + diff
        }
        if (suffix !== undefined) {
            diff = diff + ' ' + suffix
        }
    } else if (diffSeconds < (60 * 60 * 60)) {
        diff = diffHours > 1 ? diffHours + ' hours' : diffHours + ' hour'
        if (prefix !== undefined) {
            diff = prefix + ' ' + diff
        }
        if (suffix !== undefined) {
            diff = diff + ' ' + suffix
        }
    } else  {
        diff = diffDays > 1 ? diffDays + ' days' : diffDays + ' day'
        if (prefix !== undefined) {
            diff = prefix + ' ' + diff
        }
        if (suffix !== undefined) {
            diff = diff + ' ' + suffix
        }
    } 

    return diff
}