// The simplest tests, validating that it's possible to render the app at all.
describe('landing page', () => {
    it('should render', () => {
        cy.visit('/');
        cy.contains('Poradnia');
    });
});
