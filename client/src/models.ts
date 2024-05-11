export interface Item {
  name: string;
  description: string;
}

export interface Actor {
  name: string;
  backstory: string;
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

// TODO: copy event types from server
export interface GameEvent {
  type: string;
}
