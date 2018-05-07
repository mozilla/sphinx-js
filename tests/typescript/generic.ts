/**
 * Generic class with type expressions
 * @param T Type
 * @param K keys of T
 */
class Generic<T, K extends keyof T> {
    /** Optional entry of T */
    K?: T[K]
}