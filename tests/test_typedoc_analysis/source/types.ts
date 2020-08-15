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

function objProps(a: {label: string}) {
}

interface Interface {
  label: string;
  [someProp: number]: string;
  readonly readOnlyNum: number;
}

function interfacer(a: Interface) {
}

let option: {a: number; b?: string};

interface FunctionInterface {
  (thing: string, ding: number): boolean;
  additionalCallableProperty(): void;
}

interface StringArray {
  [index: number]: string;
}

// Functions. Basic function types are covered by ConvertNodeTests.test_function.

function noThis(this: void) {
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

// This has a creative default value: " aryIdentity(['str'])".
const identityString = aryIdentity(['str']);

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

