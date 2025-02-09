let desmosCalculator;

function initializeDesmosCalculator() {
    const element = document.getElementById('desmos-calculator');

    if (!desmosCalculator && element)
        desmosCalculator = Desmos.GraphingCalculator(element);
}

function plotGraph(equations) {
    initializeDesmosCalculator();

    if (!Array.isArray(equations)) {
        if (equations && equations.equations)
            equations = equations.equations;
        else
            equations = [equations];
    }

    equations.forEach(equation => {
        const exprId = `graph-${Date.now()}`;
        desmosCalculator.setExpression({ id: exprId, latex: String(equation.equation || equation) });
    });
}
