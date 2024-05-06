import { Divider, List } from '@mui/material';
import React, { useEffect, useRef } from 'react';
import { Maybe } from '@apextoaster/js-utils';
import { EventItem } from './events';

export interface HistoryPanelProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  history: Array<any>;
  scroll: 'auto' | 'instant' | 'smooth' | false;
}

export function HistoryPanel(props: HistoryPanelProps) {
  const { history, scroll } = props;
  const scrollRef = useRef<Maybe<Element>>(undefined);

  useEffect(() => {
    if (scrollRef.current && scroll !== false) {
      scrollRef.current.scrollIntoView({ behavior: scroll as ScrollBehavior, block: 'end' });
    }
  }, [scrollRef.current, props.scroll]);

  const items = history.map((item, index) => {
    if (index === history.length - 1) {
      return <EventItem key={`item-${index}`} event={item} focusRef={scrollRef} />;
    }

    return <EventItem key={`item-${index}`} event={item} />;
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
