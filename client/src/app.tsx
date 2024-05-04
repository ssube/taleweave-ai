/* eslint-disable no-restricted-syntax */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect } from 'react';
import useWebSocketModule, { ReadyState } from 'react-use-websocket';
import { Maybe, Optional, doesExist } from '@apextoaster/js-utils';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import Divider from '@mui/material/Divider';
import ListItemText from '@mui/material/ListItemText';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import Container from '@mui/material/Container';
import Stack from '@mui/material/Stack';
import Alert from '@mui/material/Alert';
import Switch from '@mui/material/Switch';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import { CssBaseline, PaletteMode, ThemeProvider, createTheme } from '@mui/material';

import { formatters } from './format.js';

const useWebSocket = (useWebSocketModule as any).default;

export interface EventItemProps {
  event: any;
}

const statusStrings = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Running',
  [ReadyState.CLOSING]: 'Closing',
  [ReadyState.CLOSED]: 'Closed',
  [ReadyState.UNINSTANTIATED]: 'Unready',
};

export function interleave(arr: Array<any>) {
  // eslint-disable-next-line @typescript-eslint/no-magic-numbers
  return arr.reduce((acc, val, idx) => acc.concat(val, <Divider component='li' key={`sep-${idx}`} variant='inset' />), []).slice(0, -1);
}

export function ActionItem(props: EventItemProps) {
  const { event } = props;
  const { actor, room, type } = event;
  const content = formatters[type](event);

  return <ListItem alignItems="flex-start">
    <ListItemAvatar>
      <Avatar alt={actor} src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary={room}
      secondary={
        <React.Fragment>
          <Typography
            sx={{ display: 'block' }}
            component="span"
            variant="body2"
            color="text.primary"
          >
            {actor}
          </Typography>
          {content}
        </React.Fragment>
      }
    />
  </ListItem>;
}

export function WorldItem(props: EventItemProps) {
  const { event } = props;
  const { step, world } = event;
  const { theme } = world;

  return <ListItem alignItems="flex-start">
    <ListItemAvatar>
      <Avatar alt={step} src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary={theme}
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >
          Step {step}
        </Typography>
      }
    />
  </ListItem>;
}

export function MessageItem(props: EventItemProps) {
  const { event } = props;
  const { message } = event;

  return <ListItem alignItems="flex-start">
    <ListItemAvatar>
      <Avatar alt="System" src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary="System"
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >
          {message}
        </Typography>
      }
    />
  </ListItem>;
}

export function EventItem(props: EventItemProps) {
  const { event } = props;
  const { type } = event;

  switch (type) {
    case 'action':
    case 'result':
      return <ActionItem event={event} />;
    case 'event':
      return <MessageItem event={event} />;
    case 'world':
      return <WorldItem event={event} />;
    default:
      return <ListItem>
        <ListItemText primary={`Unknown event type: ${type}`} />
      </ListItem>;
  }
}

export interface AppProps {
  socketUrl: string;
}

export interface Item {
  name: string;
  description: string;
}

export interface Actor {
  name: string;
  description: string;
  items: Array<Item>;
}

export interface Room {
  name: string;
  description: string;
  portals: Record<string, string>;
  actors: Array<Actor>;
  items: Array<Item>;
}

export interface World {
  name: string;
  order: Array<string>;
  rooms: Array<Room>;
  theme: string;
}

export function WorldPanel(props: { world: Maybe<World> }) {
  const { world } = props;

  return <Stack direction="column">
    <Typography variant="h4">
      World: {world?.name}
    </Typography>
    <Typography variant="h6">
      Theme: {world?.theme}
    </Typography>
    <SimpleTreeView>
      {world?.rooms.map((room) => <TreeItem itemId={room.name} label={room.name}>
        {room.actors.map((actor) => <TreeItem itemId={actor.name} label={actor.name}>
          {actor.items.map((item) => <TreeItem itemId={item.name} label={item.name} />
          )}
        </TreeItem>
        )}
        {room.items.map((item) => <TreeItem itemId={item.name} label={item.name} />
        )}
      </TreeItem>
      )}
    </SimpleTreeView>
  </Stack>;
}

export function App(props: AppProps) {
  const [ world, setWorld ] = useState<Maybe<World>>(undefined);
  const [ themeMode, setThemeMode ] = useState('light');
  const [ history, setHistory ] = useState<Array<string>>([]);
  const { lastMessage, readyState } = useWebSocket(props.socketUrl);

  const theme = createTheme({
    palette: {
      mode: themeMode as PaletteMode,
    },
  });

  const connectionStatus = statusStrings[readyState as ReadyState];

  useEffect(() => {
    if (doesExist(lastMessage)) {
      const data = JSON.parse(lastMessage.data);
      setHistory((prev) => prev.concat(data));

      // if we get a world event, update the last world state
      if (data.type === 'world') {
        setWorld(data.world);
      }
    }
  }, [lastMessage]);

  const items = history.map((item, index) => <EventItem key={`item-${index}`} event={item} />);

  return <ThemeProvider theme={theme}>
    <CssBaseline />
    <Container maxWidth='lg'>
      <Stack direction="row">
        <WorldPanel world={world} />
        <Stack direction="column">
          <Alert icon={false} severity="success">
            <Stack direction="row" alignItems="center" gap={4}>
              <Typography>
                Status: {connectionStatus}
              </Typography>
              <Switch
                checked={themeMode === 'dark'}
                onChange={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
                inputProps={{ 'aria-label': 'controlled' }}
                sx={{ marginLeft: 'auto' }}
              />
            </Stack>
          </Alert>
          <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
            {interleave(items)}
          </List>
        </Stack>
      </Stack>
    </Container>
  </ThemeProvider>;
}
