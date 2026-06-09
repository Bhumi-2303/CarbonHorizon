/**
 * Organizations API service — no logic yet, stubs only.
 */
export const organizationsApi = {
  list: () => {
    // TODO: GET /organizations
    throw new Error('Not implemented')
  },

  getById: (_id: number) => {
    // TODO: GET /organizations/:id
    throw new Error('Not implemented')
  },

  create: (_payload: unknown) => {
    // TODO: POST /organizations
    throw new Error('Not implemented')
  },

  update: (_id: number, _payload: unknown) => {
    // TODO: PATCH /organizations/:id
    throw new Error('Not implemented')
  },

  remove: (_id: number) => {
    // TODO: DELETE /organizations/:id
    throw new Error('Not implemented')
  },
}

export default organizationsApi
