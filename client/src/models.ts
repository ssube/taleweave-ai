export interface Item {
  type: 'item';
  name: string;
  description: string;
}

export interface Actor {
  type: 'actor';
  name: string;
  backstory: string;
  description: string;
  items: Array<Item>;
}

export interface Portal {
  type: 'portal';
  name: string;
  description: string;
  destination: string;
}

export interface Room {
  type: 'room';
  name: string;
  description: string;
  actors: Array<Actor>;
  items: Array<Item>;
  portals: Array<Portal>;
}

export interface World {
  type: 'world';
  name: string;
  order: Array<string>;
  rooms: Array<Room>;
  theme: string;
}

// TODO: copy event types from server
export interface GameEvent {
  type: string;
}
