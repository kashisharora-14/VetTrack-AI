import { useEffect, useMemo, useState } from 'react'
import {
  Sparkles,
  Droplets,
  UtensilsCrossed,
  Salad,
  Flame,
  Circle,
  CheckCircle2,
  Drumstick,
  Fish,
  Carrot,
  Wheat,
  Apple,
  Leaf,
  Egg,
  Trophy,
} from 'lucide-react'

const activityFactors = {
  low: 1.2,
  moderate: 1.4,
  high: 1.7,
}

const goalAdjustments = {
  'Weight Loss': 0.85,
  'Weight Gain': 1.15,
  Maintenance: 1,
  'Muscle Building': 1.1,
}

const macroProfiles = {
  'Weight Loss': { protein: 0.35, fats: 0.3, carbs: 0.35 },
  'Weight Gain': { protein: 0.25, fats: 0.25, carbs: 0.5 },
  Maintenance: { protein: 0.3, fats: 0.3, carbs: 0.4 },
  'Muscle Building': { protein: 0.4, fats: 0.25, carbs: 0.35 },
}

const foodOptionsByAnimal = {
  Dog: [
    { name: 'Lean chicken breast', icon: Drumstick },
    { name: 'Brown rice', icon: Wheat },
    { name: 'Pumpkin puree', icon: Carrot },
    { name: 'Salmon oil', icon: Fish },
    { name: 'Carrots', icon: Carrot },
    { name: 'Low-fat yogurt', icon: Egg },
  ],
  Cat: [
    { name: 'Turkey thigh', icon: Drumstick },
    { name: 'Egg whites', icon: Egg },
    { name: 'Pumpkin puree', icon: Carrot },
    { name: 'Sardines in water', icon: Fish },
    { name: 'Spinach', icon: Leaf },
    { name: 'Bone broth', icon: UtensilsCrossed },
  ],
  Rabbit: [
    { name: 'Timothy hay', icon: Wheat },
    { name: 'Romaine lettuce', icon: Leaf },
    { name: 'Bell pepper', icon: Carrot },
    { name: 'Parsley', icon: Leaf },
    { name: 'Pellets (measured)', icon: UtensilsCrossed },
    { name: 'Cilantro', icon: Leaf },
  ],
  Bird: [
    { name: 'High-quality pellets', icon: UtensilsCrossed },
    { name: 'Leafy greens', icon: Leaf },
    { name: 'Cooked quinoa', icon: Wheat },
    { name: 'Carrot shreds', icon: Carrot },
    { name: 'Apple slices', icon: Apple },
    { name: 'Millet (limited)', icon: Wheat },
  ],
}

const microNutrients = {
  Dog: ['Omega-3', 'Calcium', 'Vitamin D', 'Zinc'],
  Cat: ['Taurine', 'Omega-3', 'Vitamin A', 'B-complex'],
  Rabbit: ['Fiber', 'Calcium', 'Vitamin A', 'Manganese'],
  Bird: ['Vitamin A', 'Calcium', 'Iodine', 'Vitamin E'],
}

const round = (value) => Math.round(value)

const AnimalFoodPlanManager = () => {
  const [form, setForm] = useState({
    animalType: 'Dog',
    age: 3,
    currentWeight: 20,
    targetWeight: 18,
    activityLevel: 'moderate',
    fitnessGoal: 'Weight Loss',
    durationWeeks: 8,
  })
  const [markedFoods, setMarkedFoods] = useState([])

  const result = useMemo(() => {
    const baseRer = 70 * Math.pow(form.currentWeight, 0.75)
    const maintenanceCalories = baseRer * activityFactors[form.activityLevel]
    const adjustedCalories = maintenanceCalories * goalAdjustments[form.fitnessGoal]
    const profile = macroProfiles[form.fitnessGoal]

    const proteinCalories = adjustedCalories * profile.protein
    const fatCalories = adjustedCalories * profile.fats
    const carbCalories = adjustedCalories * profile.carbs

    const proteinGrams = proteinCalories / 4
    const fatGrams = fatCalories / 9
    const carbGrams = carbCalories / 4

    const mealsPerDay = form.animalType === 'Cat' ? 3 : form.animalType === 'Bird' ? 2 : 2
    const waterMl = form.currentWeight * 55
    const weeklyDelta = form.targetWeight > 0 ? (form.targetWeight - form.currentWeight) / form.durationWeeks : 0
    const foods = foodOptionsByAnimal[form.animalType] || foodOptionsByAnimal.Dog
    const nutrients = microNutrients[form.animalType] || microNutrients.Dog

    const aiSummary = `For a ${form.age}-year-old ${form.animalType.toLowerCase()} with a ${form.fitnessGoal.toLowerCase()} goal, the plan targets ${round(adjustedCalories)} kcal/day across ${mealsPerDay} feedings with a ${round(proteinGrams)}g protein focus.`

    return {
      maintenanceCalories: round(maintenanceCalories),
      totalCalories: round(adjustedCalories),
      proteinGrams: round(proteinGrams),
      fatGrams: round(fatGrams),
      carbGrams: round(carbGrams),
      nutrients,
      foods,
      mealsPerDay,
      waterMl: round(waterMl),
      weeklyDelta: Number(weeklyDelta.toFixed(2)),
      aiSummary,
    }
  }, [form])

  useEffect(() => {
    setMarkedFoods([])
  }, [form.animalType])

  const foodPlanScore = useMemo(() => {
    const totalFoods = result.foods.length || 1
    return round((markedFoods.length / totalFoods) * 100)
  }, [markedFoods.length, result.foods.length])

  const onValueChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const toggleFoodMark = (foodName) => {
    setMarkedFoods((prev) =>
      prev.includes(foodName) ? prev.filter((item) => item !== foodName) : [...prev, foodName]
    )
  }

  return (
    <section className="mb-6 assessment-card">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight">Animal Food Plan Manager</h2>
          <p className="mt-1 text-sm text-slate-500">Dynamic nutrition guidance using activity, goals, and target outcomes.</p>
        </div>
        <span className="chip"><Sparkles size={16} /> Mock AI Planner</span>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="text-sm font-medium text-slate-600">
          Animal type
          <select
            value={form.animalType}
            onChange={(e) => onValueChange('animalType', e.target.value)}
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:border-brand-500 focus:outline-none"
          >
            <option>Dog</option>
            <option>Cat</option>
            <option>Rabbit</option>
            <option>Bird</option>
          </select>
        </label>

        <label className="text-sm font-medium text-slate-600">
          Age (years)
          <input
            type="number"
            min="0.5"
            step="0.5"
            value={form.age}
            onChange={(e) => onValueChange('age', Number(e.target.value))}
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:border-brand-500 focus:outline-none"
          />
        </label>

        <label className="text-sm font-medium text-slate-600">
          Current weight (kg)
          <input
            type="number"
            min="0.5"
            step="0.1"
            value={form.currentWeight}
            onChange={(e) => onValueChange('currentWeight', Number(e.target.value))}
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:border-brand-500 focus:outline-none"
          />
        </label>

        <label className="text-sm font-medium text-slate-600">
          Target weight (kg)
          <input
            type="number"
            min="0"
            step="0.1"
            value={form.targetWeight}
            onChange={(e) => onValueChange('targetWeight', Number(e.target.value))}
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:border-brand-500 focus:outline-none"
          />
        </label>

        <label className="text-sm font-medium text-slate-600">
          Activity level
          <select
            value={form.activityLevel}
            onChange={(e) => onValueChange('activityLevel', e.target.value)}
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:border-brand-500 focus:outline-none"
          >
            <option value="low">Low</option>
            <option value="moderate">Moderate</option>
            <option value="high">High</option>
          </select>
        </label>

        <label className="text-sm font-medium text-slate-600">
          Fitness goal
          <select
            value={form.fitnessGoal}
            onChange={(e) => onValueChange('fitnessGoal', e.target.value)}
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:border-brand-500 focus:outline-none"
          >
            <option>Weight Loss</option>
            <option>Weight Gain</option>
            <option>Maintenance</option>
            <option>Muscle Building</option>
          </select>
        </label>

        <label className="text-sm font-medium text-slate-600">
          Diet duration (weeks)
          <input
            type="number"
            min="1"
            max="52"
            value={form.durationWeeks}
            onChange={(e) => onValueChange('durationWeeks', Number(e.target.value))}
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-700 focus:border-brand-500 focus:outline-none"
          />
        </label>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
          <p className="font-semibold text-slate-700">Expected weekly change</p>
          <p className="mt-1">{result.weeklyDelta === 0 ? 'No target delta set' : `${result.weeklyDelta} kg/week`}</p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <article className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="flex items-center gap-2 text-sm font-semibold text-slate-700"><Flame size={16} className="text-brand-600" /> Total daily calories</p>
          <p className="mt-2 text-2xl font-extrabold text-slate-900">{result.totalCalories} kcal</p>
          <p className="mt-1 text-xs text-slate-500">Maintenance baseline: {result.maintenanceCalories} kcal</p>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="flex items-center gap-2 text-sm font-semibold text-slate-700"><Salad size={16} className="text-brand-600" /> Macro breakdown</p>
          <ul className="mt-2 space-y-1 text-sm text-slate-600">
            <li>Protein: {result.proteinGrams} g/day</li>
            <li>Fats: {result.fatGrams} g/day</li>
            <li>Carbs: {result.carbGrams} g/day</li>
          </ul>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="flex items-center gap-2 text-sm font-semibold text-slate-700"><UtensilsCrossed size={16} className="text-brand-600" /> Suggested foods</p>
          <div className="mt-3 space-y-2">
            {result.foods.map((food) => {
              const isMarked = markedFoods.includes(food.name)
              const FoodIcon = food.icon || UtensilsCrossed
              return (
                <button
                  key={food.name}
                  onClick={() => toggleFoodMark(food.name)}
                  className={`flex w-full items-center justify-between rounded-xl border px-3 py-2 text-sm transition ${
                    isMarked ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <span className="grid h-7 w-7 place-items-center rounded-lg border border-slate-200 bg-white">
                      <FoodIcon size={14} className="text-brand-600" />
                    </span>
                    {food.name}
                  </span>
                  <span className="flex items-center gap-1 text-xs font-semibold">
                    {isMarked ? <CheckCircle2 size={15} /> : <Circle size={15} />}
                    {isMarked ? 'Marked' : 'Mark'}
                  </span>
                </button>
              )
            })}
          </div>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-sm font-semibold text-slate-700">Feeding frequency</p>
          <p className="mt-2 text-sm text-slate-600">{result.mealsPerDay} meals/day</p>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="flex items-center gap-2 text-sm font-semibold text-slate-700"><Droplets size={16} className="text-brand-600" /> Water intake</p>
          <p className="mt-2 text-sm text-slate-600">{result.waterMl} ml/day (approx.)</p>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-semibold text-slate-700">Important micronutrients</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {result.nutrients.map((nutrient) => (
              <span key={nutrient} className="rounded-full border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600">{nutrient}</span>
            ))}
          </div>
        </article>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="flex items-center gap-2 text-sm font-semibold text-slate-700"><Trophy size={16} className="text-brand-600" /> Food Plan Score</p>
          <span className="rounded-full bg-brand-50 px-3 py-1 text-sm font-bold text-brand-600">{foodPlanScore}%</span>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-600 transition-all duration-300"
            style={{ width: `${foodPlanScore}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Score updates as you mark suggested foods: {markedFoods.length}/{result.foods.length} completed.
        </p>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500">AI Summary Explanation</h3>
        <p className="mt-2 text-sm text-slate-700">{result.aiSummary}</p>
      </div>
    </section>
  )
}

export default AnimalFoodPlanManager
