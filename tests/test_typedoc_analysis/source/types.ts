// Basic types: https://www.typescriptlang.org/docs/handbook/basic-types.html

enum Color{
  Red = 1,
  Green = 2
}

let bool: boolean;
let num: number;
let str: string;
let array: number[];
let genericArray: Array<number>;
let tuple: [string, number];
let color: Color;
let unk: unknown;
let whatever: any;
let voidy: void;
let undef: undefined;
let nully: null;
let nev: never;
let obj: object;
let sym: symbol;


// Interfaces (https://www.typescriptlang.org/docs/handbook/interfaces.html)

interface Interface {
  readonly readOnlyNum: number;
  [someProp: number]: string;  // Just a smoketest for now. (IOW, make sure the analysis engine doesn't crash on it.) We'll need more work to handle members with no names.
}

function interfacer(a: Interface) {
}

interface FunctionInterface {
  (thing: string, ding: number): boolean;  // just a smoketest for now
}

// Functions. Basic function types are covered by ConvertNodeTests.test_function.

function noThis(this: void) {  // smoketest
}

// Make sure multi-signature functions don't crash us:
function overload(x: string[]): number;
function overload(x: number): number;
function overload(x): any {}

// Literal types (https://www.typescriptlang.org/docs/handbook/literal-types.html)

type CertainNumbers = 1 | 2 | 4;
let certainNumbers: CertainNumbers = 2;

// Unions and intersections (https://www.typescriptlang.org/docs/handbook/unions-and-intersections.html)

let union: number | string | Color = Color.Red;

interface FooHaver {
  foo: string;
}

interface BarHaver {
  bar: string;
}

let intersection: FooHaver & BarHaver;

// Generics (https://www.typescriptlang.org/docs/handbook/generics.html)

function aryIdentity<T>(things: T[]): T[] {
  console.log(things.length);
  return things;
}

class GenericNumber<T> {
  add: (x: T, y: T) => T;
}

// Generic constraints:

interface Lengthwise {
  length: number;
}

function constrainedIdentity<T extends Lengthwise>(arg: T): T {
  return arg;
}

function getProperty<T, K extends keyof T>(obj: T, key: K) {
  return obj[key];
}

function create<T>(c: { new (): T }): T {
  return new c();
}

// Utility types (https://www.typescriptlang.org/docs/handbook/utility-types.html)

let partial: Partial<string>;

// Complex: nested nightmares that show our ability to handle compound typing constructs

function objProps(a: {label: string}) {
}

let option: {a: number; b?: string};
