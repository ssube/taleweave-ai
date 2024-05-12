import { Maybe } from '@apextoaster/js-utils';
import { Divider, List } from '@mui/material';
import React, { useEffect, useRef } from 'react';
import { useStore } from 'zustand';
import { EventItem } from './events';
import { StoreState, store } from './store';

export function historyStateSelector(s: StoreState) {
  return {
    history: s.eventHistory,
    scroll: s.autoScroll,
  };
}

export interface HistoryPanelProps {
  renderEntity: (type: string, entity: string) => void;
  renderEvent: (event: string) => void;
}

export function HistoryPanel(props: HistoryPanelProps) {
  const state = useStore(store, historyStateSelector);
  const { history, scroll } = state;

  const scrollRef = useRef<Maybe<Element>>(undefined);

  const scrollBehavior = state.scroll ? 'smooth' : 'auto';

  useEffect(() => {
    if (scrollRef.current && scroll !== false) {
      scrollRef.current.scrollIntoView({ behavior: scrollBehavior, block: 'end' });
    }
  }, [scrollRef.current, scrollBehavior]);

  const items = history.map((item, index) => {
    if (index === history.length - 1) {
      return <EventItem {...props} key={`item-${index}`} event={item} focusRef={scrollRef} />;
    }

    return <EventItem {...props} key={`item-${index}`} event={item} />;
  });

  return <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
    {interleave(items)}
  </List>;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function interleave(arr: Array<any>) {
  // eslint-disable-next-line @typescript-eslint/no-magic-numbers
  return arr.reduce((acc, val, idx) => acc.concat(val, <Divider component='li' key={`sep-${idx}`} variant='inset' />), []).slice(0, -1);
}
